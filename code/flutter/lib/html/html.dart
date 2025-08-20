import 'dart:convert';
import 'package:http/http.dart' as http;

/// Sends the user's answers to Node-RED at /submit
/// chosenAnswers is a List<String> where index 1 = traffic, index 2 = weather
class NodeRedService {
  // Example: for Android emulator use 10.0.2.2; for iOS simulator you can use 'http://localhost:1880'
  final String nodeRedBase; // e.g. 'http://10.0.2.2:1880'

  NodeRedService({required this.nodeRedBase});

  Future<bool> sendAnswers({
    required List<String> chosenAnswers,
    required String region, // e.g. 'Lahore'
  }) async {
    // Safety: ensure we have enough items in chosenAnswers
    if (chosenAnswers.length <= 2) {
      // invalid input
      return false;
    }

    // Use tryParse to avoid exceptions from invalid strings
    final trafficAnswer = int.tryParse(chosenAnswers[1]) ?? 0;
    final weatherAnswer = int.tryParse(chosenAnswers[2]) ?? 0;

    // Build JSON payload exactly as Node-RED Function expects
    final payload = <String, dynamic>{
      'region': region,
      'traffic': trafficAnswer,
      'weather': weatherAnswer,
      // include ISO timestamp (optional — Node-RED will accept and can use it)
      'timestamp': DateTime.now().toUtc().toIso8601String(),
    };

    final uri = Uri.parse('$nodeRedBase/submit');

    try {
      final response = await http
          .post(
        uri,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(payload),
      )
          .timeout(const Duration(seconds: 8)); // basic timeout

      // Node-RED HTTP In -> HTTP Response should return 2xx on success
      if (response.statusCode >= 200 && response.statusCode < 300) {
        return true;
      } else {
        // optionally log: response.statusCode, response.body
        return false;
      }
    } catch (e) {
      // network error, timeout, etc.
      // optionally log e
      return false;
    }
  }
}
