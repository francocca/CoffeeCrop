import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/main.dart';
import 'package:coffecrop/models/actividad.dart';
import 'package:coffecrop/models/finca.dart';

import 'fakes/fake_finca_repository.dart';

void main() {
  testWidgets('sin finca registrada muestra el estado vacío', (tester) async {
    final repository = FakeFincaRepository();

    await tester.pumpWidget(CoffeCropApp(repository: repository));
    await tester.pump();
    await tester.pump();

    expect(find.text('Todavía no registraste tu finca'), findsOneWidget);
    expect(find.text('Registrar mi finca'), findsOneWidget);
    expect(find.byIcon(Icons.add), findsOneWidget);
  });

  testWidgets('con finca y actividades muestra datos reales', (tester) async {
    final repository = FakeFincaRepository(
      finca: Finca(
        id: 'f1',
        nombre: 'Finca La Esperanza',
        numeroPlantas: 1200,
        fechaCreacion: DateTime(2026, 1, 1),
      ),
    );
    repository.actividades.add(Actividad(
      id: 'a1',
      fincaId: 'f1',
      nombre: 'Compra de fungicida',
      monto: 150000,
      fecha: DateTime.now().subtract(const Duration(days: 3)),
      fechaCreacion: DateTime(2026, 1, 1),
    ));

    await tester.pumpWidget(CoffeCropApp(repository: repository));
    await tester.pump();
    await tester.pump();

    expect(find.text('Finca La Esperanza'), findsOneWidget);
    expect(find.text('1200 plantas de café'), findsOneWidget);
    expect(find.text('Compra de fungicida'), findsOneWidget);
    expect(find.text('Costo por planta'), findsNothing);
  });
}
