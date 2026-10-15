import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/main.dart';
import 'package:coffecrop/models/actividad.dart';
import 'package:coffecrop/models/finca.dart';
import 'package:coffecrop/screens/actividad_form_screen.dart';
import 'package:coffecrop/screens/actividades_list_screen.dart';
import 'package:coffecrop/utils/formatters.dart';

import '../fakes/fake_finca_repository.dart';

Finca _finca() => Finca(
      id: 'f1',
      nombre: 'Finca La Esperanza',
      numeroPlantas: 1200,
      fechaCreacion: DateTime(2026, 1, 1),
    );

Actividad _actividad({String nombre = 'Compra de fungicida', double monto = 150000}) => Actividad(
      id: 'a1',
      fincaId: 'f1',
      nombre: nombre,
      monto: monto,
      fecha: DateTime.now().subtract(const Duration(days: 3)),
      fechaCreacion: DateTime(2026, 1, 1),
    );

Future<void> _pasar(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump(const Duration(milliseconds: 500));
}

Future<void> _abrirApp(WidgetTester tester, FakeFincaRepository repository) async {
  await tester.pumpWidget(CoffeCropApp(repository: repository));
  await _pasar(tester);
}

void main() {
  testWidgets('el botón + abre el formulario; al guardar, Inicio muestra la actividad y el total (BR-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());
    await _abrirApp(tester, repository);
    expect(find.text('Compra de fungicida'), findsNothing);

    await tester.tap(find.byType(FloatingActionButton));
    await _pasar(tester);
    expect(find.byType(ActividadFormScreen), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).at(0), 'Compra de fungicida');
    await tester.enterText(find.byType(TextFormField).at(1), '150000');
    await tester.tap(find.text('Guardar'));
    await _pasar(tester);

    expect(find.byType(ActividadFormScreen), findsNothing);
    expect(find.text('Compra de fungicida'), findsOneWidget);
    // El monto aparece en la tarjeta de la finca (total) y en la actividad.
    expect(find.text(formatCOP(150000)), findsNWidgets(2));
  });

  testWidgets('el botón + sin finca registrada pide crearla primero (BR-005)', (tester) async {
    final repository = FakeFincaRepository();
    await _abrirApp(tester, repository);

    await tester.tap(find.byType(FloatingActionButton));
    await _pasar(tester);

    expect(find.text('Primero registrá tu finca'), findsOneWidget);
  });

  testWidgets('"Ver todas las actividades" abre el listado; al borrar y volver, Inicio se actualiza (BR-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())..actividades.add(_actividad());
    await _abrirApp(tester, repository);
    expect(find.text('Compra de fungicida'), findsOneWidget);

    await tester.tap(find.text('Ver todas las actividades'));
    await _pasar(tester);
    expect(find.byType(ActividadesListScreen), findsOneWidget);

    await tester.tap(find.byIcon(Icons.delete_outline));
    await _pasar(tester);
    await tester.tap(find.text('Eliminar'));
    await _pasar(tester);

    await tester.pageBack();
    await _pasar(tester);

    expect(find.byType(ActividadesListScreen), findsNothing);
    expect(find.text('Compra de fungicida'), findsNothing);
    expect(find.textContaining('Todavía no registraste actividades'), findsOneWidget);
  });

  testWidgets('con finca y sin actividades, la tarjeta muestra su estado vacío (US-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());

    await _abrirApp(tester, repository);

    expect(find.textContaining('Todavía no registraste actividades'), findsOneWidget);
    expect(find.text('Ver todas las actividades'), findsNothing);
  });

  testWidgets('la tarjeta muestra la fecha relativa de cada actividad (US-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())..actividades.add(_actividad());

    await _abrirApp(tester, repository);

    expect(find.text('Hace 3 días'), findsOneWidget);
  });
}
