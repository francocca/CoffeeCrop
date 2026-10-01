import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

import '../data/exceptions/finca_exceptions.dart';
import '../data/repositories/finca_repository.dart';
import '../models/finca.dart';
import '../theme/app_colors.dart';

/// Formulario para registrar o editar la finca — US-001.
class FincaFormScreen extends StatefulWidget {
  final FincaRepository repository;
  final Finca? fincaExistente;

  const FincaFormScreen({
    super.key,
    required this.repository,
    this.fincaExistente,
  });

  @override
  State<FincaFormScreen> createState() => _FincaFormScreenState();
}

class _FincaFormScreenState extends State<FincaFormScreen> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nombreController;
  late final TextEditingController _plantasController;

  String? _errorGeneral;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    _nombreController = TextEditingController(text: widget.fincaExistente?.nombre ?? '');
    _plantasController = TextEditingController(
      text: widget.fincaExistente?.numeroPlantas.toString() ?? '',
    );
  }

  @override
  void dispose() {
    _nombreController.dispose();
    _plantasController.dispose();
    super.dispose();
  }

  Future<void> _guardar() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _guardando = true;
      _errorGeneral = null;
    });

    try {
      final finca = Finca(
        id: widget.fincaExistente?.id ?? const Uuid().v4(),
        nombre: _nombreController.text.trim(),
        numeroPlantas: int.parse(_plantasController.text.trim()),
        fechaCreacion: widget.fincaExistente?.fechaCreacion ?? DateTime.now(),
      );
      await widget.repository.guardarFinca(finca);
      if (mounted) Navigator.of(context).pop(finca);
    } on InvalidFarmDataException catch (e) {
      setState(() => _errorGeneral = e.message);
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final esEdicion = widget.fincaExistente != null;
    return Scaffold(
      backgroundColor: AppColors.scaffoldBackground,
      appBar: AppBar(
        title: Text(esEdicion ? 'Editar finca' : 'Registrar finca'),
        backgroundColor: AppColors.scaffoldBackground,
        elevation: 0,
      ),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              if (_errorGeneral != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: AppColors.expense.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(_errorGeneral!, style: const TextStyle(color: AppColors.expense)),
                ),
                const SizedBox(height: 16),
              ],
              TextFormField(
                controller: _nombreController,
                decoration: const InputDecoration(
                  labelText: 'Nombre de la finca',
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  final texto = value?.trim() ?? '';
                  if (texto.isEmpty) return 'El nombre es obligatorio.';
                  if (texto.length > 100) return 'Máximo 100 caracteres.';
                  return null;
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _plantasController,
                decoration: const InputDecoration(
                  labelText: 'Número de plantas de café',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  final texto = value?.trim() ?? '';
                  final numero = int.tryParse(texto);
                  if (numero == null) return 'Ingresá un número válido.';
                  if (numero <= 0) return 'Debe ser mayor a 0.';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              FilledButton(
                onPressed: _guardando ? null : _guardar,
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: _guardando
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Text('Guardar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
