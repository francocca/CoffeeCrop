import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

/// Pantalla temporal para las secciones que todavía no se construyen.
class PlaceholderScreen extends StatelessWidget {
  final String titulo;

  const PlaceholderScreen({super.key, required this.titulo});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: Center(
        child: Text(
          '$titulo\n(próximamente)',
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.textSecondary, fontSize: 16),
        ),
      ),
    );
  }
}
