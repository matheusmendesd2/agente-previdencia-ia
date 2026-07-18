using LegacyApi.Models;

namespace LegacyApi.Data;

public static class DbSeeder
{
    public static void Seed(AppDbContext db)
    {
        if (db.Clientes.Any()) return;

        var clientes = new List<Cliente>
        {
            new() { Id = 1, Nome = "João Silva", CpfHash = "hash_cpf_001", Email = "joao.silva@email.com" },
            new() { Id = 2, Nome = "Maria Santos", CpfHash = "hash_cpf_002", Email = "maria.santos@email.com" },
            new() { Id = 3, Nome = "Carlos Oliveira", CpfHash = "hash_cpf_003", Email = "carlos.oliveira@email.com" },
            new() { Id = 4, Nome = "Ana Costa", CpfHash = "hash_cpf_004", Email = "ana.costa@email.com" },
            new() { Id = 5, Nome = "Pedro Souza", CpfHash = "hash_cpf_005", Email = "pedro.souza@email.com" },
            new() { Id = 6, Nome = "Lucia Pereira", CpfHash = "hash_cpf_006", Email = "lucia.pereira@email.com" },
            new() { Id = 7, Nome = "Marcos Almeida", CpfHash = "hash_cpf_007", Email = "marcos.almeida@email.com" },
            new() { Id = 8, Nome = "Juliana Lima", CpfHash = "hash_cpf_008", Email = "juliana.lima@email.com" },
            new() { Id = 9, Nome = "Roberto Gomes", CpfHash = "hash_cpf_009", Email = "roberto.gomes@email.com" },
            new() { Id = 10, Nome = "Fernanda Rocha", CpfHash = "hash_cpf_010", Email = "fernanda.rocha@email.com" },
            new() { Id = 11, Nome = "Antonio Barbosa", CpfHash = "hash_cpf_011", Email = "antonio.barbosa@email.com" },
            new() { Id = 12, Nome = "Patricia Dias", CpfHash = "hash_cpf_012", Email = "patricia.dias@email.com" },
        };

        db.Clientes.AddRange(clientes);

        var apolices = new List<Apolice>
        {
            new() { ClienteId = 1, Tipo = "vida", ValorCobertura = 100000m, DataInicio = new DateTime(2020, 3, 15), Status = "ativa" },
            new() { ClienteId = 1, Tipo = "previdencia", ValorCobertura = 50000m, DataInicio = new DateTime(2019, 7, 1), Status = "ativa" },
            new() { ClienteId = 2, Tipo = "previdencia", ValorCobertura = 200000m, DataInicio = new DateTime(2018, 1, 10), Status = "ativa" },
            new() { ClienteId = 2, Tipo = "prestamista", ValorCobertura = 75000m, DataInicio = new DateTime(2021, 5, 20), Status = "ativa" },
            new() { ClienteId = 3, Tipo = "vida", ValorCobertura = 150000m, DataInicio = new DateTime(2022, 11, 5), Status = "ativa" },
            new() { ClienteId = 4, Tipo = "previdencia", ValorCobertura = 300000m, DataInicio = new DateTime(2017, 6, 30), Status = "ativa" },
            new() { ClienteId = 5, Tipo = "vida", ValorCobertura = 80000m, DataInicio = new DateTime(2023, 2, 14), Status = "ativa" },
            new() { ClienteId = 5, Tipo = "prestamista", ValorCobertura = 50000m, DataInicio = new DateTime(2022, 8, 1), Status = "cancelada" },
            new() { ClienteId = 6, Tipo = "previdencia", ValorCobertura = 150000m, DataInicio = new DateTime(2020, 9, 12), Status = "ativa" },
            new() { ClienteId = 7, Tipo = "vida", ValorCobertura = 200000m, DataInicio = new DateTime(2021, 4, 18), Status = "ativa" },
            new() { ClienteId = 7, Tipo = "previdencia", ValorCobertura = 100000m, DataInicio = new DateTime(2019, 12, 1), Status = "encerrada" },
            new() { ClienteId = 8, Tipo = "prestamista", ValorCobertura = 60000m, DataInicio = new DateTime(2023, 7, 22), Status = "ativa" },
            new() { ClienteId = 9, Tipo = "vida", ValorCobertura = 120000m, DataInicio = new DateTime(2020, 1, 8), Status = "ativa" },
            new() { ClienteId = 9, Tipo = "previdencia", ValorCobertura = 250000m, DataInicio = new DateTime(2018, 4, 15), Status = "ativa" },
            new() { ClienteId = 10, Tipo = "vida", ValorCobertura = 90000m, DataInicio = new DateTime(2022, 10, 3), Status = "ativa" },
            new() { ClienteId = 11, Tipo = "previdencia", ValorCobertura = 180000m, DataInicio = new DateTime(2020, 6, 25), Status = "ativa" },
            new() { ClienteId = 11, Tipo = "prestamista", ValorCobertura = 40000m, DataInicio = new DateTime(2021, 3, 12), Status = "cancelada" },
            new() { ClienteId = 12, Tipo = "vida", ValorCobertura = 250000m, DataInicio = new DateTime(2019, 8, 20), Status = "ativa" },
            new() { ClienteId = 12, Tipo = "previdencia", ValorCobertura = 350000m, DataInicio = new DateTime(2017, 2, 5), Status = "ativa" },
        };

        db.Apolices.AddRange(apolices);
        db.SaveChanges();
    }
}
