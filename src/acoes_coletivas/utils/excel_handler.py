"""
Utilitário para manipulação de arquivos Excel
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .logging import LoggerMixin


class ExcelHandler(LoggerMixin):
    """
    Classe para manipulação de arquivos Excel
    """
    
    def __init__(self):
        super().__init__()
    
    def read_processo_numbers(self, file_path: str, column_name: str) -> List[str]:
        """
        Lê números de processo de um arquivo Excel ou CSV
        
        Args:
            file_path: Caminho para o arquivo Excel ou CSV
            column_name: Nome da coluna com os números de processo
            
        Returns:
            Lista de números de processo
        """
        try:
            # Verificar se o arquivo existe
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Detectar tipo de arquivo baseado na extensão
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                # Ler arquivo Excel
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_extension == '.csv':
                # Ler arquivo CSV
                df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_extension}. Use .xlsx, .xls ou .csv")
            
            # Verificar se a coluna existe
            if column_name not in df.columns:
                available_columns = df.columns.tolist()
                self.logger.error(
                    "column_not_found",
                    file_path=file_path,
                    column_name=column_name,
                    available_columns=available_columns
                )
                raise ValueError(f"Coluna '{column_name}' não encontrada. Colunas disponíveis: {available_columns}")
            
            # Extrair números de processo
            processos = df[column_name].astype(str).tolist()
            
            # Remover valores NaN/None
            processos = [p for p in processos if p != 'nan' and p != 'None' and p.strip()]
            
            self.log_operation(
                "processo_numbers_read",
                file_path=file_path,
                column_name=column_name,
                total_processos=len(processos),
                file_type=file_extension
            )
            
            return processos
            
        except Exception as e:
            self.log_error(e, "read_processo_numbers", file_path=file_path, column_name=column_name)
            raise
    
    def read_excel_data(self, file_path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Lê dados completos de um arquivo Excel ou CSV
        
        Args:
            file_path: Caminho para o arquivo Excel ou CSV
            sheet_name: Nome da planilha (opcional, apenas para Excel)
            
        Returns:
            DataFrame com os dados
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Detectar tipo de arquivo baseado na extensão
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                # Ler arquivo Excel
                if sheet_name is None:
                    # Se não especificar sheet_name, pegar a primeira planilha
                    df = pd.read_excel(file_path, engine='openpyxl')
                    if isinstance(df, dict):
                        # Se retornou um dicionário, pegar a primeira planilha
                        first_sheet = list(df.keys())[0]
                        df = df[first_sheet]
                else:
                    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
            elif file_extension == '.csv':
                # Ler arquivo CSV
                df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_extension}. Use .xlsx, .xls ou .csv")
            
            self.log_operation(
                "excel_data_read",
                file_path=file_path,
                sheet_name=sheet_name,
                rows=len(df),
                columns=len(df.columns),
                file_type=file_extension
            )
            
            return df
            
        except Exception as e:
            self.log_error(e, "read_excel_data", file_path=file_path, sheet_name=sheet_name)
            raise
    
    def write_excel_data(self, data: pd.DataFrame, file_path: str, sheet_name: str = 'Dados') -> None:
        """
        Escreve dados em um arquivo Excel
        
        Args:
            data: DataFrame com os dados
            file_path: Caminho para o arquivo Excel
            sheet_name: Nome da planilha
        """
        try:
            # Criar diretório se não existir
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Escrever dados
            data.to_excel(file_path, sheet_name=sheet_name, index=False, engine='openpyxl')
            
            self.log_operation(
                "excel_data_written",
                file_path=file_path,
                sheet_name=sheet_name,
                rows=len(data),
                columns=len(data.columns)
            )
            
        except Exception as e:
            self.log_error(e, "write_excel_data", file_path=file_path, sheet_name=sheet_name)
            raise
    
    def write_multiple_sheets(self, data_dict: Dict[str, pd.DataFrame], file_path: str) -> None:
        """
        Escreve múltiplas planilhas em um arquivo Excel
        
        Args:
            data_dict: Dicionário com nome da planilha como chave e DataFrame como valor
            file_path: Caminho para o arquivo Excel
        """
        try:
            # Criar diretório se não existir
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Escrever múltiplas planilhas
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                for sheet_name, df in data_dict.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            self.log_operation(
                "multiple_sheets_written",
                file_path=file_path,
                sheets=list(data_dict.keys()),
                total_sheets=len(data_dict)
            )
            
        except Exception as e:
            self.log_error(e, "write_multiple_sheets", file_path=file_path)
            raise
    
    def convert_to_dict_list(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Converte DataFrame para lista de dicionários
        
        Args:
            df: DataFrame a ser convertido
            
        Returns:
            Lista de dicionários
        """
        try:
            # Converter NaN para None
            df = df.where(pd.notnull(df), None)
            
            # Converter para lista de dicionários
            dict_list = df.to_dict('records')
            
            self.log_operation(
                "dataframe_converted",
                total_records=len(dict_list),
                columns=len(df.columns)
            )
            
            return dict_list
            
        except Exception as e:
            self.log_error(e, "convert_to_dict_list")
            raise
    
    def validate_excel_structure(self, file_path: str, required_columns: List[str]) -> bool:
        """
        Valida a estrutura de um arquivo Excel
        
        Args:
            file_path: Caminho para o arquivo Excel
            required_columns: Lista de colunas obrigatórias
            
        Returns:
            True se a estrutura é válida
        """
        try:
            df = pd.read_excel(file_path, engine='openpyxl')
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.error(
                    "excel_validation_failed",
                    file_path=file_path,
                    missing_columns=missing_columns,
                    available_columns=df.columns.tolist()
                )
                return False
            
            self.log_operation(
                "excel_validation_passed",
                file_path=file_path,
                required_columns=required_columns
            )
            
            return True
            
        except Exception as e:
            self.log_error(e, "validate_excel_structure", file_path=file_path)
            return False
    
    def get_excel_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtém informações sobre um arquivo Excel ou CSV
        
        Args:
            file_path: Caminho para o arquivo Excel ou CSV
            
        Returns:
            Dicionário com informações do arquivo
        """
        try:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Detectar tipo de arquivo baseado na extensão
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                # Ler arquivo Excel
                df = pd.read_excel(file_path, engine='openpyxl')
                if isinstance(df, dict):
                    # Se retornou um dicionário, pegar a primeira planilha
                    first_sheet = list(df.keys())[0]
                    df = df[first_sheet]
            elif file_extension == '.csv':
                # Ler arquivo CSV
                df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_extension}. Use .xlsx, .xls ou .csv")
            
            info = {
                'file_path': file_path,
                'file_size': Path(file_path).stat().st_size,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'data_types': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'sample_data': df.head().to_dict('records'),
                'file_type': file_extension
            }
            
            self.log_operation(
                "excel_info_retrieved",
                file_path=file_path,
                rows=info['total_rows'],
                columns=info['total_columns'],
                file_type=file_extension
            )
            
            return info
            
        except Exception as e:
            self.log_error(e, "get_excel_info", file_path=file_path)
            raise
    
    def clean_processo_numbers(self, processos: List[str]) -> List[str]:
        """
        Limpa e padroniza números de processo
        
        Args:
            processos: Lista de números de processo
            
        Returns:
            Lista de números de processo limpos
        """
        try:
            cleaned_processos = []
            
            for processo in processos:
                # Converter para string e remover espaços
                processo_str = str(processo).strip()
                
                # Pular valores vazios ou inválidos
                if not processo_str or processo_str.lower() in ['nan', 'none', 'null']:
                    continue
                
                # Remover caracteres especiais desnecessários
                processo_clean = processo_str.replace(' ', '').replace('\n', '').replace('\t', '')
                
                # Adicionar à lista se não estiver vazio
                if processo_clean:
                    cleaned_processos.append(processo_clean)
            
            # Remover duplicatas mantendo a ordem
            unique_processos = list(dict.fromkeys(cleaned_processos))
            
            self.log_operation(
                "processo_numbers_cleaned",
                original_count=len(processos),
                cleaned_count=len(unique_processos),
                duplicates_removed=len(cleaned_processos) - len(unique_processos)
            )
            
            return unique_processos
            
        except Exception as e:
            self.log_error(e, "clean_processo_numbers")
            raise
    
    def read_filtered_processo_numbers(self, file_path: str, column_name: str, filters: Dict[str, Any]) -> List[str]:
        """
        Lê números de processo de um arquivo Excel ou CSV com filtros
        
        Args:
            file_path: Caminho para o arquivo Excel ou CSV
            column_name: Nome da coluna com os números de processo
            filters: Dicionário com filtros a serem aplicados
                    formato: {'coluna': 'valor'} ou {'coluna': {'startswith': 'valor'}}
            
        Returns:
            Lista de números de processo filtrados
        """
        try:
            # Verificar se o arquivo existe
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Detectar tipo de arquivo baseado na extensão
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension in ['.xlsx', '.xls']:
                # Ler arquivo Excel
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_extension == '.csv':
                # Ler arquivo CSV
                df = pd.read_csv(file_path, sep=';', encoding='utf-8')
            else:
                raise ValueError(f"Formato de arquivo não suportado: {file_extension}. Use .xlsx, .xls ou .csv")
            
            # Verificar se a coluna existe
            if column_name not in df.columns:
                available_columns = df.columns.tolist()
                self.logger.error(
                    "column_not_found",
                    file_path=file_path,
                    column_name=column_name,
                    available_columns=available_columns
                )
                raise ValueError(f"Coluna '{column_name}' não encontrada. Colunas disponíveis: {available_columns}")
            
            # Aplicar filtros
            filtered_df = df.copy()
            applied_filters = {}
            
            for col_name, filter_value in filters.items():
                if col_name not in df.columns:
                    self.logger.warning(f"Coluna de filtro '{col_name}' não encontrada. Ignorando.")
                    continue
                
                # Converter para string para comparação
                filtered_df[col_name] = filtered_df[col_name].astype(str)
                
                if isinstance(filter_value, dict):
                    # Filtro avançado
                    if 'startswith' in filter_value:
                        # Converter para string e aplicar filtro
                        col_series = pd.Series(filtered_df[col_name]).astype(str)
                        mask = col_series.str.startswith(filter_value['startswith'], na=False)
                        filtered_df = filtered_df[mask]
                        applied_filters[col_name] = f"inicia com '{filter_value['startswith']}'"
                    elif 'contains' in filter_value:
                        # Converter para string e aplicar filtro
                        col_series = pd.Series(filtered_df[col_name]).astype(str)
                        mask = col_series.str.contains(filter_value['contains'], na=False)
                        filtered_df = filtered_df[mask]
                        applied_filters[col_name] = f"contém '{filter_value['contains']}'"
                    elif 'equals' in filter_value:
                        mask = filtered_df[col_name] == filter_value['equals']
                        filtered_df = filtered_df[mask]
                        applied_filters[col_name] = f"igual a '{filter_value['equals']}'"
                    elif 'json_contains' in filter_value:
                        # Filtro especial para campos JSON que contêm um valor
                        import json
                        def json_contains(value, search_term):
                            if pd.isna(value):
                                return False
                            try:
                                if isinstance(value, str) and value.startswith('{'):
                                    parsed = json.loads(value)
                                    if isinstance(parsed, list) and len(parsed) > 0:
                                        return search_term.upper() in parsed[0].upper()
                                    elif isinstance(parsed, str):
                                        return search_term.upper() in parsed.upper()
                                return search_term.upper() in str(value).upper()
                            except:
                                return search_term.upper() in str(value).upper()
                        
                        mask = filtered_df[col_name].apply(lambda x: json_contains(x, filter_value['json_contains']))
                        filtered_df = filtered_df[mask]
                        applied_filters[col_name] = f"contém '{filter_value['json_contains']}' (JSON)"
                else:
                    # Filtro simples (igualdade)
                    mask = filtered_df[col_name] == str(filter_value)
                    filtered_df = filtered_df[mask]
                    applied_filters[col_name] = f"igual a '{filter_value}'"
            
            # Extrair números de processo
            processos = filtered_df[column_name].astype(str).tolist()
            
            # Remover valores NaN/None
            processos = [p for p in processos if p != 'nan' and p != 'None' and p.strip()]
            
            self.log_operation(
                "filtered_processo_numbers_read",
                file_path=file_path,
                column_name=column_name,
                filters_applied=applied_filters,
                total_before_filter=len(df),
                total_after_filter=len(filtered_df),
                total_processos=len(processos),
                file_type=file_extension
            )
            
            return processos
            
        except Exception as e:
            self.log_error(e, "read_filtered_processo_numbers", file_path=file_path, column_name=column_name, filters=filters)
            raise 