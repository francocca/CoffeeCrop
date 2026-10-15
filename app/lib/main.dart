import 'package:flutter/material.dart';
import 'package:intl/date_symbol_data_local.dart';

import 'data/db/database_helper.dart';
import 'data/repositories/finca_repository.dart';
import 'data/repositories/sqflite_finca_repository.dart';
import 'screens/home_shell.dart';
import 'theme/app_colors.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await initializeDateFormatting('es_CO');

  final db = await DatabaseHelper.getDatabase();
  final FincaRepository repository = SqfliteFincaRepository(db);

  runApp(CoffeCropApp(repository: repository));
}

class CoffeCropApp extends StatelessWidget {
  final FincaRepository repository;

  const CoffeCropApp({super.key, required this.repository});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CoffeCrop',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: AppColors.primary),
        scaffoldBackgroundColor: AppColors.scaffoldBackground,
        fontFamily: 'Roboto',
      ),
      home: HomeShell(repository: repository),
    );
  }
}
