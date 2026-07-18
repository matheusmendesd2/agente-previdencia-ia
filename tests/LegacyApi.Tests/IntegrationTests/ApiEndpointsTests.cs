using System.Net;
using System.Net.Http.Json;
using LegacyApi.Models;

namespace LegacyApi.Tests.IntegrationTests;

public class ApiEndpointsTests : IClassFixture<CustomWebApplicationFactory>
{
    private readonly HttpClient _client;

    public ApiEndpointsTests(CustomWebApplicationFactory factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetHealth_DeveRetornar200()
    {
        var response = await _client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task GetClienteExistente_DeveRetornar200()
    {
        var response = await _client.GetAsync("/clientes/1");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var cliente = await response.Content.ReadFromJsonAsync<Cliente>();
        Assert.NotNull(cliente);
        Assert.Equal(1, cliente.Id);
    }

    [Fact]
    public async Task GetClienteInexistente_DeveRetornar404()
    {
        var response = await _client.GetAsync("/clientes/999");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task GetApolicesDeClienteExistente_DeveRetornar200()
    {
        var response = await _client.GetAsync("/clientes/1/apolices");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var apolices = await response.Content.ReadFromJsonAsync<List<Apolice>>();
        Assert.NotNull(apolices);
        Assert.True(apolices.Count > 0);
    }

    [Fact]
    public async Task GetApolicesDeClienteInexistente_DeveRetornar404()
    {
        var response = await _client.GetAsync("/clientes/999/apolices");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task GetApoliceExistente_DeveRetornar200()
    {
        var response = await _client.GetAsync("/apolices/1");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var apolice = await response.Content.ReadFromJsonAsync<Apolice>();
        Assert.NotNull(apolice);
        Assert.Equal(1, apolice.Id);
    }

    [Fact]
    public async Task GetApoliceInexistente_DeveRetornar404()
    {
        var response = await _client.GetAsync("/apolices/999");
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task SimulacaoResgate_ComApolicePrevidenciaAtiva_DeveRetornar200()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 60,
            ValorAcumulado = 100000
        };

        var response = await _client.PostAsJsonAsync("/apolices/2/simulacao-resgate", request);
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        var resultado = await response.Content.ReadFromJsonAsync<SimulacaoResgateResponse>();
        Assert.NotNull(resultado);
        Assert.True(resultado.ValorBrutoResgate > 0);
        Assert.True(resultado.ValorLiquidoResgate > 0);
    }

    [Fact]
    public async Task SimulacaoResgate_ComApoliceVida_DeveRetornar400()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 60,
            ValorAcumulado = 100000
        };

        var response = await _client.PostAsJsonAsync("/apolices/1/simulacao-resgate", request);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }

    [Fact]
    public async Task SimulacaoResgate_ComApoliceInexistente_DeveRetornar404()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 60,
            ValorAcumulado = 100000
        };

        var response = await _client.PostAsJsonAsync("/apolices/999/simulacao-resgate", request);
        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }

    [Fact]
    public async Task SimulacaoResgate_ComDadosInvalidos_DeveRetornar400()
    {
        var request = new SimulacaoResgateRequest
        {
            TempoContribuicaoMeses = 0,
            ValorAcumulado = 100000
        };

        var response = await _client.PostAsJsonAsync("/apolices/2/simulacao-resgate", request);
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
    }
}
