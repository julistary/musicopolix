import pandas as pd
import re
from datetime import datetime
from openpyxl import Workbook
import seaborn as sns
import matplotlib.pyplot as plt


def limpiar_productos(productos):
    df_p= pd.read_csv(productos,sep = ';', header = None, encoding= 'unicode_escape')
    df_p.rename(columns = {0 : "CODIGO", 1: "DESCRIPCIO", 2:"PRECIOV", 3: "PRECIOCOMP", 4: "EXISTENCIA",
                       5: "CODIGOSUP", 6: "ULTPRECIOCOM" }, inplace=True)
    
    df_p = df_p[df_p["EXISTENCIA"] > 0.0]
    df_p = df_p.reset_index()
    df_p = df_p.drop(["index"],axis=1)

    return df_p

def string(row):
    return str(row)

def brackets(row):
    try:
        return row[0]
    except:
        return row

def str_to_date(row):
    row = str(row)
    try:
        return datetime.strptime(row, '%d/%m/%y').date()
    except:
        return datetime.strptime('1/1/10', '%d/%m/%y').date()

def limpiar_movimientos(movimiento):
    import re
    df_m = pd.read_csv(movimiento, sep = ';', header = None, encoding = 'unicode_escape')
    df_m.rename(columns = {0 : "FECHA", 1: "NUMERO", 2:"POSICION", 3: "CODIGO", 4: "INCORPORAD",
                       5: "UNIDADES", 6: "IMPORTE", 7 : "TOTIMPORTE", 
                       8: "DENOMINACI", 9: "PROVIENE", 10: "MOPROVIENE"}, inplace=True)
    
    pattern = r'(\d+/\d+/\d+)'
    df_m.FECHA = df_m.FECHA.apply(lambda x: string(x))
    df_m['FECHA'] = df_m.FECHA.apply(lambda x: re.findall(pattern, x)) 
    df_m.FECHA = df_m.FECHA.apply(lambda x: brackets(x))
    df_m.FECHA = df_m.FECHA.apply(str_to_date)

    return df_m

def devuelve_excel(df_m,df_p,fecha,marcas):
    productos_disponibles = list(df_p.CODIGO.unique())
    df_m_fecha = df_m[df_m["FECHA"] > fecha]
    vendidos_desde_fecha = list(df_m_fecha.CODIGO.unique())
    productos_no_vendidos = list(set(productos_disponibles) - set(vendidos_desde_fecha))
    
    df_p_fecha = df_p[df_p["CODIGO"].isin(productos_no_vendidos)]
    df_p_fecha.drop(["PRECIOCOMP", "CODIGOSUP"],axis=1,inplace=True)
    df_p_fecha["UNIDADES_VENDIDAS"] = 0
    df_p_fecha["STOCK_INICIAL"] = 0
    df_p_fecha["PORCENTAJE_VENDIDO"] = 0
    
    unidades_vendidas_vc = dict(df_m_fecha.CODIGO.value_counts())
    df_m_fecha_2 = df_m_fecha.drop(["NUMERO","POSICION","INCORPORAD", "IMPORTE", "TOTIMPORTE", "DENOMINACI","PROVIENE","MOPROVIENE"],axis=1)
    unidades_vendidas = df_m_fecha_2.to_dict(orient='records')
    for i in unidades_vendidas:
        for j in unidades_vendidas_vc:
            if (i['CODIGO'] == j) and (i['UNIDADES'] > 1):
                unidades_vendidas_vc[i['CODIGO']] += i['UNIDADES']-1
    productos_vendidos = list(unidades_vendidas_vc.keys())
    
    df_p_fecha_vendidos = df_p[df_p["CODIGO"].isin(productos_vendidos)]
    lista_unidades_vendidas = []
    def unidades_v(row):
        lista_unidades_vendidas.append(unidades_vendidas_vc[row])
    df_p_fecha_vendidos.CODIGO.apply(lambda x: unidades_v(x))
    df_p_fecha_vendidos["UNIDADES_VENDIDAS"] = lista_unidades_vendidas
    df_p_fecha_vendidos["STOCK_INICIAL"] = df_p_fecha_vendidos["EXISTENCIA"] + df_p_fecha_vendidos["UNIDADES_VENDIDAS"]
    df_p_fecha_vendidos["PORCENTAJE_VENDIDO"] = (df_p_fecha_vendidos["UNIDADES_VENDIDAS"] / df_p_fecha_vendidos["STOCK_INICIAL"]) 
    df_p_fecha_vendidos.drop(["CODIGOSUP","PRECIOCOMP"],axis=1,inplace=True)
    
    df_final = pd.concat([df_p_fecha, df_p_fecha_vendidos])
    df_final.sort_values(by=['PORCENTAJE_VENDIDO','EXISTENCIA'],inplace=True)
    
    lista_marcas = list(marcas.MARCA.str.upper())
    lista_para_columna_marcas = []
    for index, row in df_final.iterrows():
        a = "MARCA DESCONOCIDA"
        for marca in lista_marcas:
            if marca in row["DESCRIPCIO"]:
                a = marca
        lista_para_columna_marcas.append(a)
    df_final["MARCA"] = lista_para_columna_marcas

    def floating(row):
        try:
            return float(row)
        except:
            return row 

    df_final.PRECIOV = df_final.PRECIOV.apply(floating)
    df_final.ULTPRECIOCOM = df_final.ULTPRECIOCOM.apply(floating)

    venta = list(df_final.PRECIOV)
    compra = list(df_final.ULTPRECIOCOM)
    margen = []

    for v,c in zip(venta,compra):
        try:
            margen.append((1 - float(c)/float(v))*100)
        except: 
            margen.append("Unknown")

    df_final["MARGEN"] = margen

    return df_final 

def vc_to_dict(column):
    """
    Converts the value_counts of a column of the dataframe to a dictionary 
    Args:
        column (series): the column for which you want the value counts 
    Returns:
        The value counts in dictionary format 
    """
    vc = column.value_counts()
    vc.index = vc.index.astype(str)
    return vc.to_dict()

def subdata(min_,dict_):
    """
    Removes values from a dictionary at a lower frequency than desired 
    Args:
        min_ (int): limit value used for filtering
        dict_ (dict): dictionary to be filtered 
    Returns:
        The dictionary filtered
    """
    list_ = []
    return [value for value,freq in dict_.items() if freq > min_]

def subdata_2(min_,dict_):
    """
    Removes values from a dictionary at a lower frequency than desired 
    Args:
        min_ (int): limit value used for filtering
        dict_ (dict): dictionary to be filtered 
    Returns:
        The dictionary filtered
    """
    list_ = []
    return [value for value,freq in dict_.items() if freq < min_]

def create(df,column,list_):
    """
    Creates a subdataframe with those values of the given column present in the given list 
    Args:
        df (dataframe): dataframe to work with 
        column (series): column of the dataframe to be filtered on
        list_ (list): list with the values that are used for filtering 
    Returns:
        The subdataframe
    """
    return df[df[column].isin(list_)]

def marcas_freq(df_final):
    dict_ = vc_to_dict(df_final.MARCA)
    dict_filtered = subdata(40,dict_)
    df_final_marcas_frecuentes = create(df_final,"MARCA",dict_filtered)
    #marcas.figure.savefig("marcas_freq.svg")
    return df_final_marcas_frecuentes

def marcas_no_freq(df_final):
    dict_ = vc_to_dict(df_final.MARCA)
    dict_filtered_2 = subdata_2(2,dict_)
    df_final_marcas_no_frecuentes = create(df_final,"MARCA",dict_filtered_2)    
    return df_final_marcas_no_frecuentes