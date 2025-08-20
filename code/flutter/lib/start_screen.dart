import 'package:flutter/material.dart';

class StartScreen extends StatelessWidget {
  const StartScreen(this.startQuiz, {super.key});

  final void Function() startQuiz;

  @override
  Widget build(context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Image.asset(
            'assets/images/quiz-logo.png',
            width: 300,
            color: Colors.blueGrey,
          ),
          // Opacity(
          //   opacity: 0.6,
          //   child: Image.asset(
          //     'assets/images/quiz-logo.png',
          //     width: 300,
          //   ),
          // ),
          const SizedBox(height: 80),
          Text(
            'Provide live data for your area',
            style: TextStyle(
              color: Colors.black,
              fontSize: 24,
            ),
          ),
          Text(
              'Entries are subjective, so enter what you feel',
              style: TextStyle(
                color: Colors.black87,
                fontSize: 14,
              ),
          ),
          const SizedBox(height: 30),
          OutlinedButton.icon(
            onPressed: startQuiz,
            style: OutlinedButton.styleFrom(
              foregroundColor: Colors.black87,
            ),
            icon: const Icon(Icons.arrow_right_alt),
            label: const Text('Go!'),
          )
        ],
      ),
    );
  }
}