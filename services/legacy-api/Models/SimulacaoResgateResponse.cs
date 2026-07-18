namespace LegacyApi.Models;

public class SimulacaoResgateResponse
{
    public decimal ValorBrutoResgate { get; set; }
    public decimal ImpostoRenda { get; set; }
    public decimal ValorLiquidoResgate { get; set; }
    public string RegimeTributacao { get; set; } = string.Empty;
    public string Observacao { get; set; } = string.Empty;
}
