import sys
import re
import os
import logging
from random import Random

import pandas
import tabula
import requests
import csv

from codecs import BOM_UTF8
from pdfminer.high_level import extract_text
from pdfminer.pdfparser import PDFSyntaxError


def _parse_didi(file_path, line_count=0):
    """解析滴滴出行的行程单，表头行需要特别清洗"""
    didi_area = [266, 42.765625, 785.028125, 564.134375]
    if line_count != 0:
        didi_area[2] = 3120.003125 + 31.2375 * line_count
    dfs = tabula.read_pdf(file_path, pages="all", area=didi_area)
    num = len(dfs)
    save_data = []
    save_data.append(dfs[0])
    if num == 0:
        logging.error("no table found")
    elif 1 < num:
        for i in range(1, num):
            didi_area = [175, 42.765625, 785.028125, 564.134375]
            didi_area[2] = 3120.003125 + 31.2375 * line_count
            dfs = tabula.read_pdf(file_path, pages=i + 1, area=didi_area)
            save_data.append(dfs[0])
    # 滴滴的表头行有一些多余的换行符，导致导出的 CSV 破损
    for i in range(0, num):
        save_data[i].columns = [name.replace('\r', ' ') for name in save_data[i].columns]
    return save_data


def _parse_gaode(file_path, line_count=0):
    """解析高德地图的行程单"""
    gaode_area = [173, 37.5767, 791.3437, 559.1864]
    if line_count != 0:
        gaode_area[2] = 216.9033 + line_count * 30
    dfs = tabula.read_pdf(file_path, pages="all", area=gaode_area, stream=True)
    num = len(dfs)
    save_data = []
    save_data.append(dfs[0])
    if 0 == num:
        logging.error("no table found")
    elif 1 < num:
        for i in range(1, num):
            gaode_area = [173, 37.5767, 791.3437, 559.1864]
            gaode_area[2] = 216.9033 + line_count * 30
            dfs = tabula.read_pdf(file_path, pages=i + 1, area=gaode_area)
            save_data.append(dfs[0])

    return save_data


def _parse_shouqi(file_path, line_count=0):
    """解析首汽约车的行程单，是最难处理的一种类型"""
    shouqi_area = [153.584375, 29.378125, 817.753125, 566.365625]
    if line_count != 0:
        shouqi_area[2] = 176.64062 + 15.95379 * line_count
    dfs = tabula.read_pdf(file_path, pages="all", area=shouqi_area, stream=True)
    num = len(dfs)
    save_data = []
    save_data.append(dfs[0])
    if num == 0:
        logging.error("no table found")
    elif 1 < num:
        for i in range(1, num):
            shouqi_area = [153.584375, 29.378125, 817.753125, 566.365625]
            shouqi_area[2] = 176.64062 + 15.95379 * line_count
            dfs = tabula.read_pdf(file_path, pages=i + 1, area=shouqi_area)
            save_data.append(dfs[0])

    # df = dfs[0]

    # 对识别结果进行处理
    # 表头处理
    new_df = []
    for i in range(0, num):
        rows = save_data[i].iloc[0].values
        save_data[i].columns = [str(x).strip() + ('' if str(y).strip() == 'nan' else str(y).strip()) for x, y in
                                zip(save_data[i].columns, rows)]

        # 数据处理
        data = save_data[i].values
        row_index = range(len(data))
        new_data = []
        for x, y in zip(row_index[1::2], row_index[2::2]):
            new_row = [str(a).strip() + ('' if str(b).strip() == 'nan' else str(b).strip()) for a, b in
                       zip(data[x], data[y])]
            new_data.append(new_row)
        new_df.append(pandas.DataFrame(new_data, columns=save_data[i].columns))
    return new_df


def _parse_meituan(file_path, line_count=0):
    """解析美团打车的行程单，也是比较难处理的一种类型"""
    meituan_area = [285.7275, 41.6925, 314.7975, 571.0725]
    if line_count:
        meituan_area[2] = 314.7975 + 28.305 * line_count
    dfs = tabula.read_pdf(file_path, pages='1', area=meituan_area, stream=True)

    num = len(dfs)
    save_data = []
    save_data.append(dfs[0])
    if 0 == len(dfs):
        logging.error("no table found")
    elif 1 < len(dfs):
        for i in range(1, num):
            meituan_area = [285.7275, 41.6925, 314.7975, 571.0725]
            meituan_area[2] = 314.7975 + 28.305 * line_count
            dfs = tabula.read_pdf(file_path, pages=i + 1, area=meituan_area)
            save_data.append(dfs[0])

    # df = dfs[0]
    new_df = []
    for i in range(0, num):
        data = save_data[i].values
        row_index = range(len(data))
        new_data = []
        for x, y in zip(row_index[::2], row_index[1::2]):
            new_row = [('' if str(x).strip() == 'nan' else (str(x).strip() + ' ')) + str(y).strip() for x, y in
                       zip(data[x], data[y])]
            new_data.append(new_row)
        new_df.append(pandas.DataFrame(new_data, columns=save_data[i].columns))

    return new_df


def _parse_unknown(file_path):
    dfs = tabula.read_pdf(file_path, pages="all", stream=True)
    if 0 == len(dfs):
        logging.error("no table found")
    elif 1 < len(dfs):
        logging.warning("more than 1 table recognized")
    return dfs[0]


def _output_csv(df, output_path):
    """利用 DataFrame 自身的 API，导出到 CSV 格式"""
    # 增加 BOM 头，否则不能双击Excel 直接打开CSV
    with open(output_path, mode='wb') as output:
        output.write(BOM_UTF8)

    with open(output_path, mode='a', newline='') as output:
        for i in range(0, len(df)):
            df[i].to_csv(output, index=False)


def _output_excel(df, output_path):
    """利用 DataFrame 自身的 API，导出到 Excel 格式"""
    df.to_excel(output_path, index=False, sheet_name='Sheet1')


def _output(df, file_type, csv_file_path):
    if file_type in ['csv', 'excel']:
        exporter = getattr(sys.modules[__name__], '_output_' + file_type)
        exporter(df, csv_file_path)
    else:
        logging.error('不支持的导出文件类型，目前仅支持 CSV 和 Excel')


platform_pattern = {
    'didi': {'title_like': '滴滴出行', 'line_count_like': r'共(\d+)笔行程', 'parser': _parse_didi},
    'gaode': {'title_like': '高德地图', 'line_count_like': r'共计(\d+)单行程', 'parser': _parse_gaode},
    'shouqi': {'title_like': '首汽约车电子行程单', 'line_count_like': r'共(\d+)个行程', 'parser': _parse_shouqi},
    'meituan': {'title_like': '美团打车', 'line_count_like': r'(\d+)笔行程', 'parser': _parse_meituan}
}


def _extract_text(file_path):
    try:
        pdf_to_text = extract_text(file_path)
        return ''.join([x for x in filter(lambda x: x.strip() != '', "".join(pdf_to_text).splitlines())])
    except PDFSyntaxError as pse:
        logging.error('文件解析错误，不是一个正确的 PDF 文件')
        raise Exception('无法解析 PDF') from pse

    return ''


def _read_meta(file_path):
    """读取行程单的信息，识别平台、行数、页数等"""
    file_content = _extract_text(file_path)
    line_count = 0
    for p, pattern in platform_pattern.items():
        if re.search(pattern['title_like'], file_content):
            match = re.search(pattern['line_count_like'], file_content)
            if match:
                line_count = int(match.group(1))
            return p, line_count, pattern['parser']
    return 'unknown', 0, _parse_unknown


def _read_csv(csv_file_path):
    """读取csv文件"""
    trip_data = []
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            trip_data.append(row)
    trip_data.pop(0)  # 删除第一个title
    return trip_data


def random_str(random_length=8):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(random_length):
        str += chars[random.randint(0, length)]
    return str


def read_trip(pdf_file_path, output_type, file_save_path):
    file_name = random_str()
    csv_file_path = file_save_path + '/' + file_name + '.' + output_type
    local_pdf_path = file_save_path + '/' + file_name + '.pdf'
    r = requests.get(pdf_file_path)
    if r.status_code != 200:
        raise Exception('Wrong file address')
    with open(local_pdf_path, "wb") as file_code:
        file_code.write(r.content)

    platform, line_count, parser = _read_meta(local_pdf_path)
    df = parser(local_pdf_path, line_count)
    _output(df, output_type, csv_file_path)
    trip_data = _read_csv(csv_file_path)
    os.unlink(csv_file_path)  # 删除csv文件
    os.unlink(local_pdf_path)  # 删除pdf文件
    return {
        'trip_data': trip_data,
        'platform': platform,
    }
