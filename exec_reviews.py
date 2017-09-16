
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
from datetime import datetime
from pathlib import Path
import pandas as pd
import setting


url_review = 'https://shopping.yahooapis.jp/ShoppingWebService/V1/json/reviewSearch'

# アプリケーションidはこちらで取得
# https://e.developer.yahoo.co.jp/dashboard/
appid = setting.APPID


# 全カテゴリファイル
all_categories_file = './all_categories.csv'
# 処理済みの行数
interruption_file = './中断.txt'
# 最終目的のレビューファイル
all_reviews_file = './all_reviews.csv'


# テキストの最大・最小文字数。レビュー本文がこれより長い・短いものは読み飛ばす。
max_len = 10 ** 4
min_len = 50      # 最小1

# レビュー取得件数。最大50。APIの仕様。
num_results = 50
# カテゴリごとに取得したいレビューの件数。これを超えるまでループを回してレビューを取りに行く。
# 一度にnum_resultsずつ取ってくるが、min_lenとmax_lenの制約で数が減るので、
# こうしないと生き残るレビューの数はnum_resultsより少なくなる。
num_reviews_per_cat = 99999999


def elapsed_time(start, end):
    """
    経過時間計測
    引数は、time.time()
    """
    days, rem = divmod(end - start, 60 * 60 * 24)
    hours, rem = divmod(rem, 60 * 60)
    minutes, seconds = divmod(rem, 60)
    # return '{:0>2}d {:0>2}h {:0>2}min {:05.2f}sec'.format(int(days), int(hours),int(minutes),seconds)
    return '{}d {}h {}min {:05.2f}sec'.format(int(days), int(hours), int(minutes), seconds)


def r_get(url, dct):
    """
    リクエストを投げるのは全部この関数を使う。
    レスポンスを返す。
    """
    # ガイドラインに、１回１秒は空けろと書いてた。
    time.sleep(1)
    return requests.get(url, params=dct)


def get_reviews(cat_id):
    """
    指定したカテゴリidのレビューを返す
    """
    # 実際に返した件数
    cnt_return = 0
    # 開始位置
    start = 1


    while (cnt_return < num_reviews_per_cat):
        result = r_get(url_review, {'appid': appid, 'category_id': cat_id, 'results': num_results, 'start': start})
        if result.ok:
            rs = result.json()['ResultSet']
        else:
            print('エラーが返されました : [cat id] {} [reason] {}-{}'.format(cat_id, result.status_code, result.reason))
            # todo: どうも検索結果が１件もない場合もエラーになるかもしれない。その場合は、returnも組み合わせるように修正する。
            exit(True)
            # return False

        avl = int(rs['totalResultsAvailable'])
        pos = int(rs['firstResultPosition'])
        ret = int(rs['totalResultsReturned'])
        print('\n' + '-' * 10,
              '総ヒット数: {}, 開始位置: {}, 取得数: {} ({:.1%} | cat3))'
              .format(avl, pos, ret, (pos -1  + ret) / avl if avl != 0 else 0),
              '-' * 50,
              datetime.now().strftime('%Y/%m/%d %H:%M'))

        reviews = result.json()['ResultSet']['Result']
        for rev in reviews:
            try:
                if min_len < len(rev['Description']) < max_len:
                    cnt_return += 1
                    buff = [rev['Description'].replace('\n', '').replace(',', '、'),
                            rev['ReviewTitle'].replace('\n', '').replace(',', '、'),
                            rev['Ratings']['Rate'],
                            rev['Ratings']['Average'],
                            rev['Count']['All'],
                            rev['Recommend'],
                            rev['ReviewType'],
                            rev['Purpose'],
                            rev['SendTo']]
                    yield buff
            except KeyError:
                continue
            
        # if ret < num_results:     # これだと、なぜか指定の数よりちょっと少なく返ってきた時に終わってしまう
        if pos + ret >= avl:
            return True
        else:
            start += ret
            
        print('-' * 10, 'cnt_return: {}'.format(cnt_return), '-' * 10)


def get_rowcount(file_path):
    """"
    テキストファイルの行数を返す
    """
    p = Path(file_path)
    if p.exists():
        with open(file_path, 'r') as f:
            return sum([1 for _ in f])
    else:
        return 0


def main():
    p = Path(interruption_file)
    if p.exists():
        print('-' * 100)
        print('前回実行時に中断されたようです。')
        print('中断ファイル :', p.resolve())
        print('前回中断したところから再開する場合は [continue]、')
        print('最初からやり直す場合は [restart]、')
        print('処理を中止しする場合は [abort]')
        print('を入力してください。')
        while True:
            x = input('[continue / restart / abort] > ')

            if x == 'continue':
                with open(interruption_file, 'r') as f:
                    done_cat_row = int(f.readline().rstrip())
                    print('カテゴリファイル{}の、{}行目から再開します。'.format(all_categories_file, done_cat_row))
                    break
            elif x == 'restart':
                done_cat_row = 0
                print('最初からやり直します。')
                p_rev = Path(all_reviews_file)
                if p_rev.exists():
                    p_rev.unlink()
                break
            elif x == 'abort':
                print('処理を中止します。')
                exit(True)
            else:
                print('入力が正しくありません。[{}]'.format(x))
    else:
        done_cat_row = 0


    # 計測開始
    start = time.time()

    header = ['Description', 'ReviewTitle', 'Rate', 'Average', 'CountAll', 'Recommend',
              'ReviewType', 'Purpose', 'SendTo', 'cat1_code', 'cat2_code', 'cat3_code',
              'cat1_title_short', 'cat2_title_short', 'cat3_title_short', 'cat3_title_long']

    # 出力済みファイルの件数確認
    cnt_output_total = get_rowcount(all_reviews_file)

    # ややこしくなるので、done_cat_row による読み込み制限はしない
    df = pd.read_csv(all_categories_file)
    all_cat_cnt = len(df)
    cnt_output = 0
    output_buffer = [header]
    for index, cat in df.iterrows():
        # done_rowsでdfの行数を絞るより、全部読み込んでから読み飛ばすほうが処理カウントがわかりやすい
        if index < done_cat_row:
            continue

        print('\n\n' + '#' * 10,
              datetime.now().strftime('%Y/%m/%d %H:%M'),
              '[累計出力数] {:,d} [累計カテゴリ消化率] {:.1%} [カテゴリ] {}＞{}＞{} '
              .format(cnt_output_total + cnt_output,
                      (index + 1) / all_cat_cnt,
                      cat['カテゴリ名lv1'], cat['カテゴリ名lv2'], cat['カテゴリ名lv3']),
              '#' * 120)

        for rev in get_reviews(cat['カテゴリコードlv3']):
            buff = rev + [cat['カテゴリコードlv1'],
                          cat['カテゴリコードlv2'],
                          cat['カテゴリコードlv3'],
                          cat['カテゴリ名lv1'],
                          cat['カテゴリ名lv2'],
                          cat['カテゴリ名lv3'],
                          cat['カテゴリ名lv3_long']]
            print(buff[0])   # レビュー本文(Description)
            output_buffer.append(buff)

        # 取得したデータをファイルに出力
        with open(all_reviews_file, mode='a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerows(output_buffer)
            cnt_output += len(output_buffer)
            output_buffer = []
            # 中断ファイル更新
            with open(interruption_file, 'w') as f:
                f.write(str(index + 1) + '\n')
                f.write('catcode:{}-{}-{} title:{}'
                        .format(cat['カテゴリコードlv1'], cat['カテゴリコードlv2'], cat['カテゴリコードlv3'],
                                cat['カテゴリ名lv3_long']) + '\n')
                f.write('処理済みのカテゴリ数。こちらのファイルの行番号に対応。 : {}'.format(all_categories_file) + '\n')
                f.write('重複する場合がありますが、分析上大したことではないし、重複を取り除けば良いので細かいことはきいにしない。')
    p.unlink()

    print()
    print('処理が終了しました。', datetime.now().strftime('%Y/%m/%d %H:%M'))
    print('経過時間   :', elapsed_time(start, time.time()))
    print('累計出力数 : {:,d}'.format(cnt_output_total + cnt_output))

if __name__ == '__main__':
    main()