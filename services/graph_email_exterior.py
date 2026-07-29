import logging
import os
from typing import Any, Dict, List

from services.graph_email import GraphEmailService
from util.input_excel import gerar_nomes_candidatos_carta_exterior


class GraphEmailServiceExterior(GraphEmailService):
    """Variante para credores do exterior sem CNPJ (usa apenas o nome na busca do PDF)."""

    def _try_attach_pdfs(self, credor) -> List[Dict[str, Any]]:
        if not self.cartas_dir:
            return []
        if not os.path.isdir(self.cartas_dir):
            logging.warning(f"Diretorio de cartas nao encontrado: {self.cartas_dir}")
            return []

        candidatos = gerar_nomes_candidatos_carta_exterior(credor.nome, credor.classe)
        attachments: List[Dict[str, Any]] = []
        anexados = set()

        for filename in candidatos:
            pdf_paths = self._collect_pdf_paths_for_candidate(filename)
            if not pdf_paths:
                continue

            for idx, pdf_path in enumerate(pdf_paths, start=1):
                if pdf_path in anexados:
                    continue
                if idx == 1:
                    display_name = f"Comunicado - {credor.nome}.pdf"
                else:
                    display_name = f"Comunicado - {credor.nome} ({idx}).pdf"
                attachment = self._build_pdf_attachment(credor, pdf_path, display_name)
                if attachment:
                    attachments.append(attachment)
                    anexados.add(pdf_path)
            if attachments:
                break

        if not attachments:
            logging.error(f"Nenhum PDF encontrado para {credor.nome} nos candidatos: {candidatos}")
        else:
            logging.info(f"Total de PDFs anexados para {credor.email}: {len(attachments)}")
        return attachments
