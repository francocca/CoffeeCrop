import 'package:flutter/material.dart';

import '../data/mock_finca_data.dart';
import '../theme/app_colors.dart';
import '../utils/formatters.dart';

class ActividadesCard extends StatelessWidget {
  final List<ActividadFinca> actividades;

  const ActividadesCard({super.key, required this.actividades});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardBackground,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Últimas actividades',
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
          ),
          for (final actividad in actividades) _ActividadTile(actividad: actividad),
          const SizedBox(height: 4),
          Center(
            child: TextButton(
              onPressed: () {},
              child: const Text('Ver todas las actividades'),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActividadTile extends StatelessWidget {
  final ActividadFinca actividad;

  const _ActividadTile({required this.actividad});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.agriculture, color: AppColors.primary, size: 20),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(actividad.nombre, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                Text('Hace ${actividad.diasAtras} días', style: const TextStyle(fontSize: 12, color: AppColors.textSecondary)),
              ],
            ),
          ),
          Text(
            formatCOP(actividad.monto),
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
          ),
        ],
      ),
    );
  }
}
