import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/models/actividad.dart';
import 'package:coffecrop/models/finca.dart';
import 'package:coffecrop/screens/actividades_list_screen.dart';
import 'package:coffecrop/screens/actividad_form_screen.dart';

import '../fakes/fake_finca_repository.dart';

Finca _finca() => Finca(
      id: 'f1',
      nombre: 'Finca La Esperanza',
      numeroPlantas: 1200,
      fechaCreacion: DateTime(2026, 1, 1),
    );

/// Actividad N es más reciente cuanto mayor es N (hace [total - n + 1] días).
Actividad _actividad(int n, {int total = 1}) => Actividad(
      id: 'a$n',
      fincaId: 'f1',
      nombre: 'Actividad $n',
      monto: 1000.0 * n,
      fecha: DateTime.now().subtract(Duration(days: total - n + 1)),
      fechaCreacion: DateTime(2026, 1, 1),
    );

Future<void> _abrirLista(WidgetTester tester, FakeFincaRepository repository) async {
  await tester.pumpWidget(MaterialApp(
    home: Builder(
      builder: (context) => Scaffold(
        body: Center(
          child: ElevatedButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => ActividadesListScreen(repository: repository),
            )),
            child: const Text('abrir'),
          ),
        ),
      ),
    ),
  ));
  await tester.tap(find.text('abrir'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump(const Duration(milliseconds: 500));
}

Future<void> _pasar(WidgetTester tester) async {
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump(const Duration(milliseconds: 500));
}

void main() {
  testWidgets('sin actividades muestra el estado vacío (US-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());

    await _abrirLista(tester, repository);

    expect(find.text('Todavía no tenés actividades registradas'), findsOneWidget);
  });

  testWidgets('lista la más reciente primero con su fecha relativa (US-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())
      ..actividades.addAll([_actividad(1, total: 3), _actividad(2, total: 3), _actividad(3, total: 3)]);

    await _abrirLista(tester, repository);

    final nombres = tester
        .widgetList<Text>(find.textContaining('Actividad '))
        .map((t) => t.data)
        .toList();
    expect(nombres, ['Actividad 3', 'Actividad 2', 'Actividad 1']);
    expect(find.text('Ayer'), findsOneWidget);
    expect(find.text('Hace 3 días'), findsOneWidget);
  });

  testWidgets('pagina de a 20: carga la siguiente página al llegar al final (DEC-004)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())
      ..actividades.addAll([for (var n = 1; n <= 25; n++) _actividad(n, total: 25)]);

    await _abrirLista(tester, repository);
    expect(find.text('Actividad 25'), findsOneWidget);
    expect(find.text('Actividad 1'), findsNothing);

    await tester.scrollUntilVisible(find.text('Actividad 1'), 400);
    await _pasar(tester);

    expect(find.text('Actividad 1'), findsOneWidget);
  });

  testWidgets('eliminar pide confirmación: cancelar conserva, confirmar borra (US-005)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())
      ..actividades.addAll([_actividad(1, total: 2), _actividad(2, total: 2)]);

    await _abrirLista(tester, repository);

    await tester.tap(find.byIcon(Icons.delete_outline).first);
    await _pasar(tester);
    expect(find.text('¿Eliminar actividad?'), findsOneWidget);

    await tester.tap(find.text('Cancelar'));
    await _pasar(tester);
    expect(repository.actividades.length, 2);

    await tester.tap(find.byIcon(Icons.delete_outline).first);
    await _pasar(tester);
    await tester.tap(find.text('Eliminar'));
    await _pasar(tester);

    expect(repository.actividades.length, 1);
    expect(find.text('Actividad 2'), findsNothing);
    expect(find.text('Actividad 1'), findsOneWidget);
  });

  testWidgets('tocar una actividad abre el formulario en modo edición (US-005)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca())..actividades.add(_actividad(1));

    await _abrirLista(tester, repository);
    await tester.tap(find.text('Actividad 1'));
    await _pasar(tester);

    expect(find.byType(ActividadFormScreen), findsOneWidget);
    expect(find.text('Editar actividad'), findsOneWidget);
  });
}
