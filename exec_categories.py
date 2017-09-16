
# coding: utf-8

# # yahooショッピングのレビュー情報をapiで取得する
# 目的：自然言語処理の開発・テスト用データのため  
# https://developer.yahoo.co.jp/webapi/shopping/shopping/v1/reviewsearch.html

# In[1]:

import requests
import json
import csv
import time
import pickle
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

# エンドポイント
url_cat = 'https://shopping.yahooapis.jp/ShoppingWebService/V1/json/categorySearch'

# アプリケーションidはこちらで取得
# https://e.developer.yahoo.co.jp/dashboard/
appid = 'dj00aiZpPUVwU2tKZkhldURqWiZzPWNvbnN1bWVyc2VjcmV0Jng9M2I-'

# 最終目的の、全カテゴリファイル
all_categories_file = './all_categories.csv'

def r_get(url, dct):
    """
    リクエストを投げるのは全部この関数を使う。
    レスポンスを返す。
    """
    # ガイドラインに、１回１秒は空けろと書いてた。
    time.sleep(1)
    return requests.get(url, params=dct)


def get_cats(cat_id):
    """
    カテゴリー一覧を取得するジェネレータ。
    指定したカテゴリidの子カテゴリを返す。
    """
    try:
        result = r_get(url_cat, {'appid': appid, 'category_id': cat_id})
        cats = result.json()['ResultSet']['0']['Result']['Categories']['Children']
        for i, cat in cats.items():
            if i != '_container':
                yield cat['Id'], {'short': cat['Title']['Short'], 'medium': cat['Title']['Medium'],
                                  'long': cat['Title']['Long']}
    except:
        pass


if __name__ == '__main__':
    p = Path(all_categories_file)
    if p.exists():
        p.unlink()

    # ヘッダー
    output_buffer = [['カテゴリコードlv1', 'カテゴリコードlv2', 'カテゴリコードlv3',
                      'カテゴリ名lv1', 'カテゴリ名lv2', 'カテゴリ名lv3', 'カテゴリ名lv3_long']]

    # カテゴリレベル１ : 22個
    for id1, title1 in get_cats(1):
        print(datetime.now(), '\t', '********** カテゴリレベル１ :', title1['short'], '*' * 80)
        try:
            # カテゴリレベル２ : 335個
            for id2, title2 in get_cats(id1):
                print(datetime.now(), '\t', '---------- カテゴリレベル２ :', title2['short'], '-' * 50)

                # lカテゴリレベル３ : 約3,700個
                for id3, title3 in get_cats(id2):
                    wk = [id1, id2, id3, title1['short'], title2['short'], title3['short'], title3['long']]
                    output_buffer.append(wk)
                    print(datetime.now(), '\t',
                          '[カテゴリid] lv1:{}  lv2:{}  lv3: {}\tカテゴリ名: {} ＞ {} ＞ {} '.format(*wk))

                # これくらいのタイミングでファイルに書こうかな
                with open(all_categories_file, 'a') as f:
                    writer = csv.writer(f, lineterminator='\n')
                    writer.writerows(output_buffer)
                    output_buffer = []

        except KeyError:
            continue

    print('処理が完了しました')
