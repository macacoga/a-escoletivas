#!/usr/bin/env python3
"""
Teste do pré-processador melhorado
"""

from src.acoes_coletivas.database.manager import DatabaseManager
from src.acoes_coletivas.nlp.text_preprocessor import TextPreprocessor
import re

def test_preprocessor():
    """Testa o pré-processador melhorado"""
    
    db = DatabaseManager()
    preprocessor = TextPreprocessor()
    
    print("🔍 TESTANDO PRÉ-PROCESSADOR MELHORADO")
    print("=" * 50)
    
    # Pegar um texto problemático
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, numero_processo, conteudo_bruto_decisao 
            FROM processos_judiciais 
            WHERE id = 7973
        """)
        row = cursor.fetchone()
        
        if row:
            processo_id, numero_processo, texto_bruto = row
            print(f"📄 Processo: {numero_processo}")
            print(f"📊 Tamanho original: {len(texto_bruto):,} caracteres")
            
            # Testar apenas a função _clean_complex_html
            print("\n🧪 TESTANDO _clean_complex_html DIRETAMENTE...")
            try:
                texto_limpo_direto = preprocessor._clean_complex_html(texto_bruto)
                print(f"📊 Tamanho após _clean_complex_html: {len(texto_limpo_direto):,} caracteres")
                print(f"📋 Amostra: {texto_limpo_direto[:300]}...")
                
                if len(texto_limpo_direto) > 0:
                    qualidade = preprocessor.validate_text_quality(texto_limpo_direto)
                    print(f"⭐ Qualidade: {qualidade.get('quality_score', 0):.2f}")
                    print(f"❌ Problemas: {qualidade.get('issues', [])}")
                    
                    if qualidade.get('quality_score', 0) > 0.7:
                        print("\n✅ SUCESSO! Qualidade alta!")
                    elif qualidade.get('quality_score', 0) > 0.5:
                        print("\n⚠️  MELHORIA PARCIAL")
                    else:
                        print("\n❌ Qualidade ainda baixa")
                else:
                    print("❌ Função removeu todo o texto")
                    
            except Exception as e:
                print(f"❌ Erro em _clean_complex_html: {e}")
                import traceback
                traceback.print_exc()
            
            # Agora testar o método completo step by step
            print("\n🔧 TESTANDO MÉTODO COMPLETO STEP BY STEP...")
            try:
                # Etapa 1: HTML
                print("Etapa 1: Removendo HTML...")
                texto_step1 = preprocessor._remove_html_tags(texto_bruto)
                print(f"Tamanho após HTML: {len(texto_step1):,}")
                
                # Etapa 2: Encoding
                print("Etapa 2: Limpando encoding...")
                texto_step2 = preprocessor._clean_encoding(texto_step1)
                print(f"Tamanho após encoding: {len(texto_step2):,}")
                
                # Etapa 3: Headers/footers
                print("Etapa 3: Removendo headers/footers...")
                texto_step3 = preprocessor._remove_headers_footers(texto_step2)
                print(f"Tamanho após headers: {len(texto_step3):,}")
                
                # Etapa 4: Espaços
                print("Etapa 4: Normalizando espaços...")
                texto_step4 = preprocessor._normalize_spaces(texto_step3)
                print(f"Tamanho após espaços: {len(texto_step4):,}")
                
                # Etapa 5: Cleanup final
                print("Etapa 5: Cleanup final...")
                texto_step5 = preprocessor._final_cleanup(texto_step4, preserve_structure=True)
                print(f"Tamanho final: {len(texto_step5):,}")
                
                if len(texto_step5) > 0:
                    print(f"📋 Amostra final: {texto_step5[:300]}...")
                else:
                    print("❌ Texto foi removido em alguma etapa!")
                
            except Exception as e:
                print(f"❌ Erro no step by step: {e}")
                import traceback
                traceback.print_exc()
            
        else:
            print("❌ Processo não encontrado")

if __name__ == "__main__":
    test_preprocessor() 