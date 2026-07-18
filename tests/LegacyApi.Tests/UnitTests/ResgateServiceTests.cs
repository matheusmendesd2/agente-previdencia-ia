using LegacyApi.Models;
using LegacyApi.Services;

namespace LegacyApi.Tests.UnitTests;

public class ResgateServiceTests
{
    private readonly ResgateService _service = new();

    [Theory]
    [InlineData(12, 50000, 35)]
    [InlineData(24, 100000, 30)]
    [InlineData(36, 75000, 25)]
    [InlineData(48, 200000, 20)]
    [InlineData(60, 150000, 15)]
    [InlineData(120, 300000, 10)]
    [InlineData(240, 500000, 10)]
    public void Simular_DeveCalcularAliquotaCorreta(int meses, decimal valor, decimal aliquotaEsperada)
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = meses,
            ValorAcumulado = valor
        };

        var resultado = _service.Simular(request);

        var impostoEsperado = valor * aliquotaEsperada / 100m;
        Assert.Equal(Math.Round(impostoEsperado, 2), resultado.ImpostoRenda);
        Assert.Equal(valor - Math.Round(impostoEsperado, 2), resultado.ValorLiquidoResgate);
    }

    [Fact]
    public void Simular_ComTempoZero_DeveLancarExcecao()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 0,
            ValorAcumulado = 50000
        };

        var ex = Assert.Throws<ArgumentException>(() => _service.Simular(request));
        Assert.Contains("maior que zero", ex.Message);
    }

    [Fact]
    public void Simular_ComValorZero_DeveLancarExcecao()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 12,
            ValorAcumulado = 0
        };

        var ex = Assert.Throws<ArgumentException>(() => _service.Simular(request));
        Assert.Contains("maior que zero", ex.Message);
    }

    [Fact]
    public void Simular_TempoMenorQue60Meses_DeveRetornarObservacaoAdequada()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 36,
            ValorAcumulado = 100000
        };

        var resultado = _service.Simular(request);

        Assert.Contains("60 meses", resultado.Observacao);
    }

    [Fact]
    public void Simular_TempoMaiorQue120Meses_DeveRetornarAliquotaMinima()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 180,
            ValorAcumulado = 500000
        };

        var resultado = _service.Simular(request);

        Assert.Equal(10m, resultado.ImpostoRenda / resultado.ValorBrutoResgate * 100m, 1);
    }

    [Fact]
    public void Simular_ValorLiquido_NuncaDeveSerMaiorQueValorBruto()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 60,
            ValorAcumulado = 100000
        };

        var resultado = _service.Simular(request);

        Assert.True(resultado.ValorLiquidoResgate < resultado.ValorBrutoResgate);
        Assert.True(resultado.ValorLiquidoResgate > 0);
    }
}
