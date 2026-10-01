import 'package:intl/intl.dart';

final _currencyFormat = NumberFormat.currency(
  locale: 'es_CO',
  symbol: '\$',
  decimalDigits: 0,
);

String formatCOP(num value) => _currencyFormat.format(value);
