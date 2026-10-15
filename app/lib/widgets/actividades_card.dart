import 'package:flutter/material.dart';

import '../models/actividad.dart';
import '../theme/app_colors.dart';
import '../utils/formatters.dart';

class ActividadesCard extends StatelessWidget {
  final List<Actividad> actividades;
  final VoidCallback onVerTodas;

  const ActividadesCard({
    super.key,
    required this.actividades,
    required this.onVerTodas,
  });

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
          if (actividades.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: Text(
                'Todavía no registraste actividades. Tocá el botón + para agregar la primera.',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            )
          else ...[
            for (final actividad in actividades) _ActividadTile(actividad: actividad),
            const SizedBox(height: 4),
            Center(
              child: TextButton(
                onPressed: onVerTodas,
                child: const Text('Ver todas las actividades'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _ActividadTile extends StatelessWidget {
  final Actividad actividad;

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
                Text(
                  formatearHace(actividad.fecha),
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
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
