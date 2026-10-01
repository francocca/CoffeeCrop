import 'package:flutter/material.dart';

import '../data/mock_finca_data.dart';
import '../theme/app_colors.dart';
import '../widgets/actividades_card.dart';
import '../widgets/finca_card.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Finca - Resumen',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: AppColors.divider),
                  ),
                  child: const Icon(Icons.more_vert, size: 20),
                ),
              ],
            ),
            const SizedBox(height: 18),
            FincaCard(
              nombre: MockFincaData.nombreFinca,
              numeroPlantas: MockFincaData.numeroPlantas,
              inversionTotal: MockFincaData.inversionTotal.toDouble(),
              costoPorPlanta: MockFincaData.costoPorPlanta.toDouble(),
            ),
            const SizedBox(height: 16),
            ActividadesCard(actividades: MockFincaData.ultimasActividades),
          ],
        ),
      ),
    );
  }
}
