# Catálogo de Prometeo. Ya no se edita aquí: todo lo que se sigue está en ../seguimiento.yml
# (personas, cargos, partidos, nivel 1, cabeceras, temas, YouTube y Telegram). Este módulo solo
# lo expone con los nombres que usa prom.py.
import re
import seguimiento as S

PROV = S.PROV

def alias_re(alias):
    return re.compile(r'(?<![\wÀ-ÿ])(' + '|'.join(re.escape(a) for a in alias) + r')(?![\wÀ-ÿ])')

def catalogo(cfg=None):
    return S.catalogo(cfg)

if __name__ == '__main__':
    import json
    print(json.dumps(catalogo(), ensure_ascii=False)[:400])
