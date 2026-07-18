using LegacyApi.Models;

namespace LegacyApi.Services;

public class ResgateService
{
    private static readonly Dictionary<int, decimal> TabelaIR = new()
    {
        { 12, 35m },
        { 24, 30m },
        { 36, 25m },
        { 48, 20m },
        { 60, 15m },
        { 120, 10m },
    };

    public SimulacaoResgateResponse Simular(SimulacaoResgateRequest request)
    {
        if (request.TempoContribuicaoMeses <= 0)
            throw new ArgumentException("Tempo de contribuição deve ser maior que zero.");

        if (request.ValorAcumulado <= 0)
            throw new ArgumentException("Valor acumulado deve ser maior que zero.");

        var aliquotaIR = CalcularAliquotaIR(request.TempoContribuicaoMeses);
        var impostoRenda = request.ValorAcumulado * aliquotaIR / 100m;
        var valorLiquido = request.ValorAcumulado - impostoRenda;

        var regime = request.TempoContribuicaoMeses >= 120 ? "Regime Progressivo" : "Regime Regressivo";

        return new SimulacaoResgateResponse
        {
            ValorBrutoResgate = request.ValorAcumulado,
            ImpostoRenda = Math.Round(impostoRenda, 2),
            ValorLiquidoResgate = Math.Round(valorLiquido, 2),
            RegimeTributacao = regime,
            Observacao = GerarObservacao(aliquotaIR, request.TempoContribuicaoMeses)
        };
    }

    private static decimal CalcularAliquotaIR(int meses)
    {
        foreach (var (prazo, aliquota) in TabelaIR.OrderBy(t => t.Key))
        {
            if (meses <= prazo) return aliquota;
        }
        return 10m;
    }

    private static string GerarObservacao(decimal aliquota, int meses)
    {
        if (meses < 60)
            return "Resgate com incidência reduzida de IR disponível após 60 meses de contribuição.";
        if (meses < 120)
            return "Alíquota reduzida por tempo de contribuição. Consulte seu planejador financeiro.";
        return "Alíquota mínima de IR aplicada. Benefício de longo prazo consolidado.";
    }
}
