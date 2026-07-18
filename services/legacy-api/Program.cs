using Microsoft.EntityFrameworkCore;
using LegacyApi.Data;
using LegacyApi.Models;
using LegacyApi.Services;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddDbContext<AppDbContext>(opts =>
    opts.UseSqlite("Data Source=legacy.db"));
builder.Services.AddScoped<ResgateService>();

var app = builder.Build();

using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
    DbSeeder.Seed(db);
}

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapGet("/health", () => Results.Ok(new { status = "ok" }));

app.MapGet("/clientes/{id:int}", async (int id, AppDbContext db) =>
{
    var cliente = await db.Clientes.FindAsync(id);
    return cliente is null ? Results.NotFound(new { erro = "Cliente não encontrado" }) : Results.Ok(cliente);
});

app.MapGet("/clientes/{id:int}/apolices", async (int id, AppDbContext db) =>
{
    if (!await db.Clientes.AnyAsync(c => c.Id == id))
        return Results.NotFound(new { erro = "Cliente não encontrado" });

    var apolices = await db.Apolices.Where(a => a.ClienteId == id).ToListAsync();
    return Results.Ok(apolices);
});

app.MapGet("/apolices/{id:int}", async (int id, AppDbContext db) =>
{
    var apolice = await db.Apolices.FindAsync(id);
    return apolice is null ? Results.NotFound(new { erro = "Apólice não encontrada" }) : Results.Ok(apolice);
});

app.MapPost("/apolices/{id:int}/simulacao-resgate", async (int id, SimulacaoResgateRequest request, AppDbContext db, ResgateService resgateService) =>
{
    var apolice = await db.Apolices.FindAsync(id);
    if (apolice is null)
        return Results.NotFound(new { erro = "Apólice não encontrada" });

    if (apolice.Tipo != "previdencia")
        return Results.BadRequest(new { erro = "Simulação de resgate disponível apenas para apólices de previdência" });

    if (apolice.Status != "ativa")
        return Results.BadRequest(new { erro = "Apólice não está ativa" });

    try
    {
        var resultado = resgateService.Simular(request);
        return Results.Ok(resultado);
    }
    catch (ArgumentException ex)
    {
        return Results.BadRequest(new { erro = ex.Message });
    }
});

app.Run();
