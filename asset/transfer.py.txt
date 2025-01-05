import markdown
import base64
import sqlite3
import pandas as pd
from pandas import DataFrame

resource_path = './resource.csv'
content_path = './content.csv'


def read_dataframe() -> DataFrame:
    resource_df = pd.read_csv(resource_path)
    content_df = pd.read_csv(content_path)

    resource_df = resource_df[resource_df['type'] == 'content'].sort_values(by='id').reset_index()
    content_df = content_df.sort_values(by='id').reset_index()
    content_df['content'] = content_df['content'].apply(lambda x: markdown.markdown(base64.b64decode(x).decode()))
    content_df['content'] = content_df['content'].apply(lambda x: x.replace('\"', '\\"').replace('\'', '\\'))

    df = pd.concat([resource_df, content_df], axis=1)
    return df.drop([
        'id', 'url', 'this_url', 'owner_id', 'group_id', 'permission',
        'parent_url', 'type', 'index', 'category_id', 'sub_title'
    ], axis=1)


def generate_sql(df: DataFrame) -> list[str]:
    return ['''
        insert into wwr_blog_post (title, content, status, create_time, update_time, deleted, preview)
        values(\'{title}\', \'{content}\', \'published\', \'{create_time}\', \'{update_time}\', 0, \'\')
    '''.format(
        title=row['title'],
        content=row['content'],
        create_time=row['created_time'],
        update_time=row['updated_time']
    ) for _, row in df.iterrows()]


def insert(sql: list[str]):
    cursor = sqlite3.connect('../wwr.sqlite3')
    print(sql)
    for s in sql:
        print(s)
        cursor.execute(s)
    cursor.commit()
    cursor.close()


def main():
    df = read_dataframe()
    sql = generate_sql(df)
    insert(sql)


if __name__ == '__main__':
    main()
