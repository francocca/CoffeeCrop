import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/models/actividad.dart';
import 'package:coffecrop/models/finca.dart';
import 'package:coffecrop/screens/actividad_form_screen.dart';

import '../fakes/fake_finca_repository.dart';

Finca _finca() => Finca(
      id: 'f1',
      nombre: 'Finca La Esperanza',
      numeroPlantas: 1200,
      fechaCreacion: DateTime(2026, 1, 1),
    );

/// Abre el formulario desde una pantalla anfitriona (para poder hacer pop).
Future<void> _abrirFormulario(
  WidgetTester tester,
  FakeFincaRepository repository, {
  Actividad? actividad,
}) async {
  await tester.pumpWidget(MaterialApp(
    home: Builder(
      builder: (context) => Scaffold(
        body: Center(
          child: ElevatedButton(
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => ActividadFormScreen(
                repository: repository,
                actividadExistente: actividad,
              ),
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

Future<void> _llenar(WidgetTester tester, {String? nombre, String? monto}) async {
  if (nombre != null) await tester.enterText(find.byType(TextFormField).at(0), nombre);
  if (monto != null) await tester.enterText(find.byType(TextFormField).at(1), monto);
}

Future<void> _guardar(WidgetTester tester) async {
  await tester.tap(find.text('Guardar'));
  await tester.pump();
  await tester.pump(const Duration(milliseconds: 500));
  await tester.pump(const Duration(milliseconds: 500));
}

void main() {
  testWidgets('sin finca bloquea el registro y ofrece crearla (BR-005, DEC-003)', (tester) async {
    final repository = FakeFincaRepository();

    await _abrirFormulario(tester, repository);

    expect(find.text('Primero registrá tu finca'), findsOneWidget);
    expect(find.text('Registrar mi finca'), findsOneWidget);
    expect(find.text('Guardar'), findsNothing);
  });

  testWidgets('con finca guarda la actividad y cierra el formulario (US-003)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());

    await _abrirFormulario(tester, repository);
    await _llenar(tester, nombre: 'Compra de fungicida', monto: '150000');
    await _guardar(tester);

    expect(repository.actividades.length, 1);
    expect(repository.actividades.first.nombre, 'Compra de fungicida');
    expect(repository.actividades.first.monto, 150000);
    expect(repository.actividades.first.fincaId, 'f1');
    expect(find.byType(ActividadFormScreen), findsNothing);
  });

  testWidgets('muestra errores de validación y no guarda (BR-003)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());

    await _abrirFormulario(tester, repository);
    await _guardar(tester);

    expect(find.text('El nombre es obligatorio.'), findsOneWidget);
    expect(find.text('Ingresá un monto válido.'), findsOneWidget);
    expect(repository.actividades, isEmpty);
    expect(find.byType(ActividadFormScreen), findsOneWidget);
  });

  testWidgets('rechaza montos negativos (BR-003)', (tester) async {
    final repository = FakeFincaRepository(finca: _finca());

    await _abrirFormulario(tester, repository);
    await _llenar(tester, nombre: 'Rastrillo', monto: '-5');
    await _guardar(tester);

    expect(find.text('El monto no puede ser negativo.'), findsOneWidget);
    expect(repository.actividades, isEmpty);
  });

  testWidgets('en modo edición precarga los valores y actualiza (US-005)', (tester) async {
    final existente = Actividad(
      id: 'a1',
      fincaId: 'f1',
      nombre: 'Fertilización',
      monto: 50000,
      fecha: DateTime(2026, 1, 5),
      fechaCreacion: DateTime(2026, 1, 5),
    );
    final repository = FakeFincaRepository(finca: _finca())..actividades.add(existente);

    await _abrirFormulario(tester, repository, actividad: existente);

    expect(find.text('Editar actividad'), findsOneWidget);
    expect(find.text('Fertilización'), findsOneWidget);
    expect(find.text('50000'), findsOneWidget);

    await _llenar(tester, monto: '80000');
    await _guardar(tester);

    expect(repository.actividades.length, 1);
    expect(repository.actividades.first.id, 'a1');
    expect(repository.actividades.first.monto, 80000);
    expect(find.byType(ActividadFormScreen), findsNothing);
  });
}
