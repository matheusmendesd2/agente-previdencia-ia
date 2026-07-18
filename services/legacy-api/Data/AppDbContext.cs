using Microsoft.EntityFrameworkCore;
using LegacyApi.Models;

namespace LegacyApi.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Cliente> Clientes => Set<Cliente>();
    public DbSet<Apolice> Apolices => Set<Apolice>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Cliente>(entity =>
        {
            entity.ToTable("Clientes");
            entity.HasKey(c => c.Id);
            entity.Property(c => c.Nome).HasMaxLength(200).IsRequired();
            entity.Property(c => c.CpfHash).HasMaxLength(64).IsRequired();
            entity.Property(c => c.Email).HasMaxLength(200).IsRequired();
        });

        modelBuilder.Entity<Apolice>(entity =>
        {
            entity.ToTable("Apolices");
            entity.HasKey(a => a.Id);
            entity.Property(a => a.Tipo).HasMaxLength(50).IsRequired();
            entity.Property(a => a.ValorCobertura).HasColumnType("decimal(18,2)");
            entity.Property(a => a.Status).HasMaxLength(50).IsRequired();
            entity.HasOne(a => a.Cliente)
                  .WithMany(c => c.Apolices)
                  .HasForeignKey(a => a.ClienteId);
        });
    }
}
