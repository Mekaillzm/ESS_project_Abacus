import 'package:flutter/material.dart';

import 'package:app5/data/questions.dart';
import 'package:app5/questions_summary/questions_summary.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({
    super.key,
    required this.chosenAnswers,
    required this.onRestart,
  });

  final void Function() onRestart;
  final List<String> chosenAnswers;

  List<Map<String, Object>> getSummaryData() {
    final List<Map<String, Object>> summary = [];

    for (var i = 0; i < chosenAnswers.length; i++) {
      summary.add({
        'question_index': i,
        'question': questions[i].text,
        'correct_answer': questions[i].answers[0],
        'user_answer': chosenAnswers[i],
      });
      NodeRedService.sendChosenAnswers(chosenAnswers);
    }

    return summary;
  }

  @override
  Widget build(BuildContext context) {
    final summaryData = getSummaryData();
    final numTotalQuestions = questions.length;
    final numCorrectQuestions = summaryData.where((data) {
      return data['user_answer'] == data['correct_answer'];
    }).length;

    return SizedBox(
      width: double.infinity,
      child: Container(
        margin: const EdgeInsets.all(40),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              'Data entered successfully',
              style: TextStyle(
                color: Colors.black87,
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 30),
            QuestionsSummary(summaryData),
            const SizedBox(height: 30),
            TextButton.icon(
              onPressed: onRestart,
              style: TextButton.styleFrom(foregroundColor: Colors.black87),
              icon: const Icon(Icons.refresh),
              label: const Text('New Entry'),
            ),
          ],
        ),
      ),
    );
  }
}

// lib/services/node_red_service.dart

/// Node-RED service to POST the quiz answers to Node-RED /submit endpoint.
///
/// Usage:
///   // (optional) override default base:
///   NodeRedService.nodeRedBase = 'http://192.168.1.42:1880';
///   final ok = await NodeRedService.sendChosenAnswers(chosenAnswers);
class NodeRedService {
  /// Default: Android emulator -> host machine
  /// For iOS simulator or desktop you may use 'http://localhost:1880'
  /// For physical device use your host LAN IP: 'http://192.168.x.y:1880'
  static String nodeRedBase = 'http://10.0.2.2:1880';

  /// Posts an already-built payload map to Node-RED /submit.
  /// Returns true on HTTP 2xx, false otherwise.
  static Future<bool> sendPayload(Map<String, dynamic> payload) async {
    final uri = Uri.parse('$nodeRedBase/submit');
    try {
      final resp = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(payload),
          )
          .timeout(const Duration(seconds: 8));
      return resp.statusCode >= 200 && resp.statusCode < 300;
    } catch (e) {
      // Optionally log e
      return false;
    }
  }

  /// Convenience helper that accepts the same chosenAnswers list your ResultsScreen uses.
  ///
  /// Expects chosenAnswers layout:
  ///  index 0: region (String) e.g. "Lahore"
  ///  index 1: airQuality (String that can be parsed to int; e.g. "1" or "0")
  ///  index 2: weather (String -> int)
  ///
  /// Builds payload:
  /// {
  ///   'region': 'Lahore',
  ///   'airQuality': 1,
  ///   'weather': 0,
  ///   'timestamp': '2025-08-18T07:12:00Z'
  /// }
  static Future<bool> sendChosenAnswers(List<String> chosenAnswers) async {
    if (chosenAnswers.length <= 2) {
      return false;
    }

    final region = chosenAnswers[0];
    final airQuality = int.tryParse(chosenAnswers[1]) ?? 0;
    final weather = int.tryParse(chosenAnswers[2]) ?? 0;

    final payload = <String, dynamic>{
      'region': region,
      'airQuality': airQuality,
      'weather': weather,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
    };

    return await sendPayload(payload);
  }
}
