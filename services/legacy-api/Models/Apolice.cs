namespace LegacyApi.Models;

public class Apolice
{
    public int Id { get; set; }
    public int ClienteId { get; set; }
    public string Tipo { get; set; } = string.Empty; // vida, previdencia, prestamista
    public decimal ValorCobertura { get; set; }
    public DateTime DataInicio { get; set; }
    public string Status { get; set; } = string.Empty; // ativa, cancelada, encerrada
    public Cliente? Cliente { get; set; }
}
