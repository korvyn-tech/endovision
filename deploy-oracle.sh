#!/usr/bin/env bash
# ==============================================================================
# EndoVision - Script de Instalação e Deploy Automático para VPS Oracle Cloud
# Desenvolvido pela Korvyn &bull; Suporta Ubuntu, Debian e Oracle Linux
# ==============================================================================

set -e

echo "=========================================================="
echo "  Iniciando Deploy do EndoVision na VPS Oracle (Korvyn)"
echo "=========================================================="

# 1. Atualiza repositórios do sistema
echo "[1/5] Verificando dependências do sistema..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y
    sudo apt-get install -y curl git ufw
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf update -y
    sudo dnf install -y curl git firewalld
fi

# 2. Instala Docker se não estiver instalado
if ! command -v docker >/dev/null 2>&1; then
    echo "[2/5] Docker não encontrado. Instalando Docker automaticamente..."
    curl -fsSL https://get.docker.com | sh
    sudo systemctl enable --now docker
    sudo usermod -aG docker $USER || true
else
    echo "[2/5] Docker já está instalado."
fi

# 3. Libera as portas no firewall interno do Linux (Portas 80, 443 e 8000)
echo "[3/5] Liberando portas no firewall interno do Linux..."
if command -v ufw >/dev/null 2>&1; then
    sudo ufw allow 80/tcp || true
    sudo ufw allow 443/tcp || true
    sudo ufw allow 8000/tcp || true
elif command -v firewall-cmd >/dev/null 2>&1; then
    sudo firewall-cmd --permanent --add-port=80/tcp || true
    sudo firewall-cmd --permanent --add-port=443/tcp || true
    sudo firewall-cmd --permanent --add-port=8000/tcp || true
    sudo firewall-cmd --reload || true
fi

# Regra direta no iptables da Oracle Cloud para garantir passagem de tráfego
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT || true
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT || true

# 4. Prepara diretório de dados persistentes do SQLite
echo "[4/5] Configurando diretório de banco de dados..."
mkdir -p data

# Garante existência do arquivo .env com valores padrão se não existir
if [ ! -f .env ]; then
    echo "[!] Arquivo .env não encontrado. Criando modelo de configuração..."
    cat << 'EOF' > .env
# Chave de Produção Asaas (Cole sua chave abaixo)
ASAAS_API_KEY=
ASAAS_ENVIRONMENT=production
JWT_SECRET=korvyn_endovision_secure_jwt_secret_2026
DATABASE_URL=sqlite:////app/data/endovision.db
EOF
    echo "Por favor, adicione sua ASAAS_API_KEY no arquivo .env antes de iniciar."
fi

# 5. Compila e inicia o container com Docker Compose
echo "[5/5] Construindo e iniciando os containers do EndoVision..."
docker compose down || true
docker compose up -d --build

echo "=========================================================="
echo "  🎉 EndoVision está RODANDO COM SUCESSO!"
echo "  Porta: 8000"
echo "  Acesse: http://$(curl -s ifconfig.me):8000"
echo "=========================================================="
