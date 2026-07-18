namespace LegacyApi.Models;

public class Cliente
{
    public int Id { get; set; }
    public string Nome { get; set; } = string.Empty;
    public string CpfHash { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public List<Apolice> Apolices { get; set; } = new();
}
