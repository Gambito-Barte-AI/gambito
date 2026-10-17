"""Reprodução A7 por subprocesso instalado, fontes somente leitura e cópias isoladas."""

import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from cenarios_a7 import criar
from validar_saida import CONTRATO, ler_csv, verificar


def executar_aceite(dados, regras, saida, evidencias, python, referencia=None, minimo=None):
    for destino in (saida, evidencias):
        if destino == dados or destino.is_relative_to(dados) or destino.exists():
            raise ValueError(f"Use destino novo, separado das fontes: {destino}")
    evidencias.mkdir(parents=True)
    fora=evidencias/'execucao-fora-do-projeto';fora.mkdir()
    ambiente={k:v for k,v in os.environ.items() if k not in {'PYTHONPATH','PYTHONHOME'}
              and not any(t in k.upper() for t in ('API_KEY','TOKEN','SECRET'))}
    ambiente.update(PYTHONNOUSERSITE='1',PYTHONUTF8='1',TEMP=str(evidencias),TMP=str(evidencias))
    casos={}

    def rodar(nome, entrada, destino, config=regras, codigo=0, auditavel=True):
        inicio=time.perf_counter()
        p=subprocess.run([str(python),'-m','tarvo','--dados',str(entrada),'--saida',str(destino),
                          '--regras',str(config),'--escopo','alvo'],cwd=fora,env=ambiente,
                          capture_output=True,text=True,encoding='utf-8',timeout=60)
        (evidencias/(nome+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
        if p.returncode != codigo:raise AssertionError(f'{nome}: retorno {p.returncode}, esperado {codigo}; consulte o log')
        m=json.loads((destino/'manifesto.json').read_text(encoding='utf-8'))
        if auditavel:
            auditoria=verificar(entrada,destino,config)
        else:
            from auditoria_integrada import verificar as global_
            from validar_saida import verificar_partes
            verificar_partes(m)
            arquivos={n:ler_csv(destino/n,c) for n,c in CONTRATO.items()}
            global_(m,arquivos)
            assert m['situacao_comando']=='BLOQUEADO' and not any(arquivos.values())
            auditoria={'integridade_estrutural':True,'financeira':'Não disponível sem configuração; todos os resultados bloqueados'}
        (evidencias/(nome+'-auditoria.json')).write_text(json.dumps(auditoria,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        casos[nome]=dict(retorno=p.returncode,duracao_segundos=round(time.perf_counter()-inicio,3),
            partes={k:v['situacao'] for k,v in m['partes'].items()},auditoria=auditoria)
        print(nome+': OK',flush=True)
        return m

    antes={p.name:sha256(p.read_bytes()).hexdigest() for p in dados.iterdir() if p.is_file()}
    base=rodar('completo',dados,saida)
    assert base['fechamento']['situacao']=='COMPLETO'
    rodar('repeticao',dados,evidencias/'repeticao')
    for n in (*CONTRATO,'manifesto.json'):
        assert (saida/n).read_bytes()==(evidencias/'repeticao'/n).read_bytes(),f'Determinismo: {n}'
    if referencia:
        for n in CONTRATO:assert (saida/n).read_bytes()==(referencia/n).read_bytes(),f'Regressão A1–A6: {n}'
    p=subprocess.run([str(python),'-m','tarvo','--dados',str(dados),'--saida',str(evidencias/'minimo'),
                      '--regras',str(regras)],cwd=fora,env=ambiente,capture_output=True,text=True,encoding='utf-8',timeout=60)
    (evidencias/'minimo.log').write_text(p.stdout+p.stderr,encoding='utf-8')
    assert p.returncode==0
    verificar(dados,evidencias/'minimo',regras,'COMPLETO')
    if minimo:
        for n in CONTRATO:assert (evidencias/'minimo'/n).read_bytes()==(minimo/n).read_bytes(),f'Regressão do mínimo: {n}'
    familias={
        'orbe':{'CHECKOUT','PENDENCIAS_CHECKOUT','DIVERGENCIAS_CHECKOUT','DEVOLUCAO_CASA','NOTAS_CHECKOUT'},
        'taxas':{'CHECKOUT','PENDENCIAS_CHECKOUT','DIVERGENCIAS_CHECKOUT','DEVOLUCAO_CASA','NOTAS_CHECKOUT','REMESSAS','DIVERGENCIAS_REMESSA','NOTAS_REMESSA'},
        'ponte':{'REMESSAS','DIVERGENCIAS_REMESSA','NOTAS_REMESSA'},
        'plano_contas':{'EXTRATO_AURORA','EXTRATO_MERIDIANO'},'aurora':{'EXTRATO_AURORA'},'meridiano':{'EXTRATO_MERIDIANO'}}
    if 'ALERTAS_ANTECIPACAO' in base['partes']:
        familias['orbe'].add('ALERTAS_ANTECIPACAO');familias['taxas'].add('ALERTAS_ANTECIPACAO')
    nomes={f:[x['arquivo'] for x in base['fontes'][f]['arquivos']] if f in {'orbe','ponte'} else [base['fontes'][f]['arquivo']] for f in familias}
    faltantes={}
    for fonte in familias:
        for layout in (False,True):
            nome=('layout-' if layout else 'sem-')+fonte
            copia=evidencias/('dados-'+nome);shutil.copytree(dados,copia)
            for arquivo in nomes[fonte]:
                alvo=copia/arquivo
                if not layout:alvo.unlink()
                elif fonte=='orbe':alvo.write_text('id_transacao;layout_novo\nX;?\n',encoding='utf-8')
                elif fonte=='aurora':alvo.write_text('Banco Aurora S.A.\nLayout incompatível\n',encoding='utf-8')
                elif fonte=='plano_contas':alvo.write_text('COD_CONTA;DESCRICAO\nX;Layout incompatível\n',encoding='utf-8')
                else:alvo.write_bytes(b'Layout incompativel')
            m=rodar(nome,copia,evidencias/nome,codigo=2)
            for parte in set(base['partes'])-familias[fonte]:
                assert m['partes'][parte]['situacao']==base['partes'][parte]['situacao'],f'{nome}: bloqueio indevido de {parte}'
            if fonte=='taxas':
                assert m['partes']['CHECKOUT']['situacao']=='BLOQUEADO'
                assert m['partes']['DIVERGENCIAS_REMESSA']['situacao']=='BLOQUEADO'
                assert m['partes']['REMESSAS']['rastro_validado'] and m['partes']['NOTAS_REMESSA']['rastro_validado']
            else:
                assert all(m['partes'][p]['situacao']=='BLOQUEADO' for p in familias[fonte])
            if not layout:faltantes[fonte]=copia
    vazio=evidencias/'dados-vazios';vazio.mkdir()
    rodar('dados-vazios',vazio,evidencias/'vazio',codigo=1)
    rodar('sem-configuracao',dados,evidencias/'sem-configuracao',config=evidencias/'nao-existe.toml',codigo=1,auditavel=False)
    reuso=evidencias/'reuso'
    rodar('reuso-completo',dados,reuso)
    rodar('reuso-sem-ponte',faltantes['ponte'],reuso,codigo=2)
    for n in ('comissoes_por_lojista.csv','notas_a_emitir.csv','divergencias_taxa.csv'):
        assert not any(l['linha_negocio']=='REMESSA' for l in ler_csv(reuso/n,CONTRATO[n])),f'Saída antiga reapareceu: {n}'
    sintetico=evidencias/'outubro-sintetico';sintetico.mkdir()
    entradas,config=criar(sintetico)
    m=rodar('outubro-sintetico',entradas,sintetico/'saida',config=config)
    assert m['competencia']=='2032-10' and m['fechamento']['situacao']=='COMPLETO'
    tardio=entradas/'chegada_tardia.csv';bruto=tardio.read_bytes();tardio.unlink()
    rodar('antes-do-tardio',entradas,sintetico/'chegada',config=config)
    tardio.write_bytes(bruto)
    m=rodar('depois-do-tardio',entradas,sintetico/'chegada',config=config)
    assert m['cobertura']['linhas_lidas']==7
    assert antes=={p.name:sha256(p.read_bytes()).hexdigest() for p in dados.iterdir() if p.is_file()}
    resultado=dict(aprovado=True,casos=casos,determinismo=True,regressao_a1_a6=bool(referencia),
        regressao_minimo=bool(minimo),fontes_preservadas=True,saidas={n:base['resultados'][n]['linhas'] for n in CONTRATO})
    (evidencias/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return resultado


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('dados','regras','saida','evidencias'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--python',type=Path,default=Path(sys.executable))
    p.add_argument('--referencia',type=Path);p.add_argument('--minimo',type=Path)
    a=p.parse_args()
    try:
        executar_aceite(a.dados.resolve(),a.regras.resolve(),a.saida.resolve(),a.evidencias.resolve(),a.python.resolve(),
                       a.referencia.resolve() if a.referencia else None,a.minimo.resolve() if a.minimo else None)
    except (AssertionError,ValueError,OSError,subprocess.SubprocessError) as exc:
        p.exit(1,f'A7 REPROVADA: {exc}\n')


if __name__=='__main__':main()
