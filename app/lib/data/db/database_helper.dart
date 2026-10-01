import 'package:path/path.dart';
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

class DatabaseHelper {
  static const _dbName = 'coffecrop.db';
  static const _dbVersion = 1;

  static Database? _database;

  static Future<Database> getDatabase() async {
    _database ??= await _open();
    return _database!;
  }

  static Future<Database> _open() async {
    final documentsDir = await getApplicationDocumentsDirectory();
    final path = join(documentsDir.path, _dbName);

    return openDatabase(
      path,
      version: _dbVersion,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE finca (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            numero_plantas INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL
          );
        ''');

        await db.execute('''
          CREATE TABLE actividad (
            id TEXT PRIMARY KEY,
            finca_id TEXT NOT NULL,
            nombre TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (finca_id) REFERENCES finca(id)
          );
        ''');
      },
    );
  }
}
