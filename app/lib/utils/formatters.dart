import 'package:intl/intl.dart';

final _currencyFormat = NumberFormat.currency(
  locale: 'es_CO',
  symbol: '\$',
  decimalDigits: 0,
);

String formatCOP(num value) => _currencyFormat.format(value);

/// "Hoy", "Ayer" o "Hace N días" según los días calendario transcurridos.
String formatearHace(DateTime fecha, {DateTime? ahora}) {
  final hoy = ahora ?? DateTime.now();
  final dias = DateTime(hoy.year, hoy.month, hoy.day)
      .difference(DateTime(fecha.year, fecha.month, fecha.day))
      .inDays;
  if (dias <= 0) return 'Hoy';
  if (dias == 1) return 'Ayer';
  return 'Hace $dias días';
}
