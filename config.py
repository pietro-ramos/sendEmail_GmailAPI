# Configurações de envio de e-mail
REMETENTE = 'naoresponda@rdv-insolvencia.com'
IMAGEM_PATH = 'data/Imagem1.png'
ASSUNTO = "Informações Importantes para Credores"
TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comunicado</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
        }}
        .centered {{
            text-align: center;
        }}
        .bold {{
            font-weight: bold;
        }}
    </style>
</head>
<body>

    <p>Prezado credor,</p>

    <p>Informamos que o <strong>Plano de Recuperação Judicial</strong> do grupo Gramado Parks foi homologado em <strong>30/10/2024</strong>. A partir da homologação do plano, iniciaram-se os prazos para cumprimento e pagamento do seu crédito.</p>

    <p>A RDV, na condição de Administradora Judicial do processo, informa que os credores elegíveis têm o prazo de <strong>30 dias</strong> para informar às empresas a sua opção por uma das condições de pagamento previstas no Plano de Recuperação Judicial aprovado. Dito isso, você deve informar seus dados bancários, ou chave PIX, e sua opção de pagamento às Recuperandas, por correspondência escrita endereçada ao local abaixo descrito, ou de forma eletrônica através do e-mail referido:</p>

    <p class="centered"><strong>GRUPO GRAMADO PARKS</strong><br>
    A/C DEPARTAMENTO FINANCEIRO<br>
    Rua Santa Maria, n.º 193, bairro Carniel,<br>
    Município de Gramado/RS, CEP: 95.670-000.<br>
    <strong>E-mail: <a href="mailto:recuperacao.judicial@gramadoparks.com">recuperacao.judicial@gramadoparks.com</a></strong></p>

    <p>O Plano de Recuperação Judicial em questão, bem como as principais informações do processo, podem ser verificadas no site da Administração Judicial: <a href="https://rdv-insolvencia.com/processos/gramado-parks/" target="_blank">https://rdv-insolvencia.com/processos/gramado-parks/</a></p>

    <p>Atenciosamente,</p>

    <img src="cid:imagem1" alt="Imagem RDV" />

</body>
</html>
"""

# Caminho do arquivo Excel
ARQUIVO_EMAILS = 'data/credores.xlsx'
ARQUIVO_RELATORIO = 'relatorio_bounces.xlsx'
