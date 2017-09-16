# YahooショッピングのレビューデータをAPIで取得する
## 準備
1. アプリケーションidを取得する  
https://e.developer.yahoo.co.jp/dashboard/
1. カレントディレクトリに `setting.py` を作成して、アプリケーションIDを設定する  
```python
APPID = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```
## 使い方
### 1.カテゴリ一覧を作成する
[api仕様](https://developer.yahoo.co.jp/webapi/shopping/shopping/v1/categorysearch.html)  
`exec_categories.py` を実行する。  
-> `all_categories.csv` に、カテゴリー３レベルのすべてのカテゴリが出力される。

### 2.レビューデータを取得する
[api仕様](https://developer.yahoo.co.jp/webapi/shopping/shopping/v1/reviewsearch.html)  
`exec_reviews.py` を実行する。  
-> `all_reviews.csv` に、レビューデータが出力される。

**`all_reviews.csv`**
|ヘッダカラム名|内容|
|:---|:---|
|Description|レビューの本文|
|ReviewTitle|レビューのタイトル文（例：購入しました！）|
|Rate|レビュー評価点 : 1.00（悪い）から5.00（良い）|
|Average|レビュー平均点|
|CountAll|レビュー数|
|Recommend|レビューを見て役立った人の数|
|ReviewType|レビューの種類 : buyer（購入者）/other（クチコミ）/all（全員）|
|Purpose|購入目的 : daily（購入者）/hobby（趣味用途）/gift（プレゼント）/business（仕事用）|
|SendTo|誰用に購入したか : self（自分用）/family（家族親戚用）/friend（友人へ）/lover（彼氏彼女へ）/business（取引先へ）|
|cat1_code|レベル1カテゴリid|
|cat2_code|レベル2カテゴリid|
|cat3_code|レベル3カテゴリid|
|cat1_title_short|レベル1カテゴリ名|
|cat2_title_short|レベル2カテゴリ名|
|cat3_title_short|レベル3カテゴリ名|
|cat3_title_long|親カテゴリを含むカテゴリ名|

## コツ、注意
- APIの利用制限  
１日のリクエスト回数が上限を超えた時にステータスコード403でエラーになります。AM0:00でリセットされるので、それまで待ちましょう。
https://developer.yahoo.co.jp/appendix/rate.html
- 中断、分割実行
    - エラー、手動中断等理由を問わず、処理が中断されても、その中断したカテゴリIDから再開することが出来ます。
    (カレントディレクトリに `中断.txt` というファイルが作成されています。)
    - `中断.txt`を作成し、１行目に `all_categories.csv` のカテゴリの行番号を指定すると、その次の行から実行出来ます。

<!-- Begin Yahoo! JAPAN Web Services Attribution Snippet -->
<a href="https://developer.yahoo.co.jp/about">
<img src="https://s.yimg.jp/images/yjdn/yjdn_attbtn2_88_35.gif" width="88" height="35" title="Webサービス by Yahoo! JAPAN" alt="Webサービス by Yahoo! JAPAN" border="0" style="margin:15px 15px 15px 15px"></a>
<!-- End Yahoo! JAPAN Web Services Attribution Snippet -->
