"""Read XLSX/XLSM XML cells only. No macros, external links or formulas execute."""
import posixpath
from zipfile import ZipFile
from xml.etree import ElementTree as ET

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RID = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'


def sheets(path):
    with ZipFile(path) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            for item in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', NS):
                strings.append(''.join(t.text or '' for t in item.findall('.//s:t', NS)))
        relations = {r.attrib['Id']: r.attrib['Target'] for r in
                      ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
                      if r.attrib.get('TargetMode') != 'External'}
        for sheet in ET.fromstring(archive.read('xl/workbook.xml')).findall('s:sheets/s:sheet', NS):
            target = relations[sheet.attrib[RID]]
            member = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            rows = {}
            for row in ET.fromstring(archive.read(member)).findall('s:sheetData/s:row', NS):
                cells = {}
                for cell in row.findall('s:c', NS):
                    value = cell.findtext('s:v', default=None, namespaces=NS)
                    kind = cell.attrib.get('t')
                    if kind == 's' and value is not None:
                        value = strings[int(value)]
                    elif kind == 'inlineStr':
                        value = ''.join(t.text or '' for t in cell.findall('.//s:t', NS))
                    formula = cell.findtext('s:f', default=None, namespaces=NS)
                    if value is not None or formula is not None:
                        cells[cell.attrib['r']] = dict(value=value, formula=formula, type=kind)
                if cells:
                    rows[int(row.attrib['r'])] = cells
            yield sheet.attrib['name'], rows
