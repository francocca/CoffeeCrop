/// Datos de finca inválidos — corresponde a BR-001 de spec.md.
class InvalidFarmDataException implements Exception {
  final String message;
  const InvalidFarmDataException(this.message);

  @override
  String toString() => message;
}

/// Datos de actividad inválidos — corresponde a BR-003 de spec.md.
class InvalidActivityDataException implements Exception {
  final String message;
  const InvalidActivityDataException(this.message);

  @override
  String toString() => message;
}

/// Se intentó registrar una actividad sin una finca creada — corresponde a BR-005 de spec.md.
class NoFincaException implements Exception {
  final String message;
  const NoFincaException([this.message = 'Primero debes registrar tu finca.']);

  @override
  String toString() => message;
}
