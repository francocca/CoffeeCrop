import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:coffecrop/main.dart';

void main() {
  testWidgets('CoffeCropApp arranca y muestra la pantalla de Inicio', (WidgetTester tester) async {
    await tester.pumpWidget(const CoffeCropApp());
    await tester.pumpAndSettle();

    expect(find.text('Finca - Resumen'), findsOneWidget);
    expect(find.byIcon(Icons.add), findsOneWidget);
  });
}
