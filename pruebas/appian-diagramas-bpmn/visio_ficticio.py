"""Un Visio (.vsdx) mínimo y ficticio con un proceso BPMN de una página, para probar «importar» y «comparar --con»."""
import zipfile
NS='http://schemas.microsoft.com/office/visio/2012/main'
def shape(i,master,text,x,y,w=1,h=0.6):
    return f'<Shape ID="{i}" Master="{master}" Type="Shape"><Cell N="PinX" V="{x}"/><Cell N="PinY" V="{y}"/><Cell N="Width" V="{w}"/><Cell N="Height" V="{h}"/><Text>{text}</Text></Shape>'
def conn(i,text=""):
    return f'<Shape ID="{i}" Master="9" Type="Shape"><Cell N="PinX" V="0"/><Cell N="PinY" V="0"/>' + (f'<Text>{text}</Text>' if text else '') + '</Shape>'
def construir(ruta):
    masters={1:"Pool / Lane",2:"Start Event",3:"Task",4:"Gateway",5:"End Event",9:"Sequence Flow",6:"Text Annotation"}
    shapes=[shape(10,1,"Solicitante",6,8,12,2), shape(11,1,"Técnico",6,6,12,2), shape(12,1,"Registro mercantil",6,4,12,1.5),
            shape(20,2,"Solicitud recibida",1,8), shape(21,3,"Registrar solicitud",3,8), shape(22,3,"Revisar solicitud",5,6),
            shape(23,4,"¿Completa?",7,6), shape(24,5,"Solicitud aprobada",9,6), shape(25,5,"Solicitud devuelta",9,8),
            shape(26,6,"Plazo de 10 días",5,7),
            conn(30),conn(31),conn(32),conn(33,"Sí"),conn(34,"No"),conn(35,"Consulta"),conn(36)]
    cx=[(30,20,21),(31,21,22),(32,22,23),(33,23,24),(34,23,25),(35,22,12),(36,26,22)]
    connects="".join(f'<Connect FromSheet="{c}" FromCell="BeginX" ToSheet="{a}"/><Connect FromSheet="{c}" FromCell="EndX" ToSheet="{b}"/>' for c,a,b in cx)
    page=f'<PageContents xmlns="{NS}"><Shapes>{"".join(shapes)}</Shapes><Connects>{connects}</Connects></PageContents>'
    pages=f'<Pages xmlns="{NS}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><Page ID="0" NameU="Solicitud de alta"><Rel r:id="rId1"/></Page></Pages>'
    rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page1.xml"/></Relationships>'
    mast=f'<Masters xmlns="{NS}">'+"".join(f'<Master ID="{k}" NameU="{v}"/>' for k,v in masters.items())+'</Masters>'
    with zipfile.ZipFile(ruta,"w") as z:
        z.writestr("visio/pages/pages.xml",pages); z.writestr("visio/pages/_rels/pages.xml.rels",rels)
        z.writestr("visio/pages/page1.xml",page); z.writestr("visio/masters/masters.xml",mast)
