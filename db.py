import sqlite3

class MyDb(object):
	def __init__(self, name):
		self.name = name

	def execute(self, cmd, args=''):
		con = sqlite3.connect(self.name)
		cur = con.cursor()

		cur = cur.execute(cmd, args)
		con.commit()

	def create_table_cmd(self, table_name, table_values):
		fmst = f'CREATE TABLE IF NOT EXISTS {table_name} ({table_values[0]} PRIMARY KEY, {",".join(table_values[1:])})'
		return fmst

	def insert_to_table_cmd(self, table_name, table_values):
		number_or_args = len(table_values)
		fmst = f"INSERT OR REPLACE INTO {table_name} VALUES ({','.join(['?']*number_or_args)})"
		return fmst

	def build_db(self, table_name, args):
		table_cmd = self.create_table_cmd(table_name, args)
		print(table_cmd)
		self.execute(table_cmd)

	def insert_to_table(self, table_name, values):
		cmd = self.insert_to_table_cmd(table_name, values)
		self.execute(cmd, values)


	def print_table(self, table_name, limit=None):
		music= sqlite3.connect(self.name)
		cur = music.cursor()
		cur.row_factory = sqlite3.Row
		limit_cmd = f' LIMIT {limit}' if limit else ''
		select_cmd = f"SELECT * from {table_name}{limit_cmd}"
		for r in cur.execute(select_cmd):
			for k in r.keys():
				print(f'{k} - {r[k]}')

	def get_all(self, table_name):
		con = sqlite3.connect(self.name)
		con.row_factory = sqlite3.Row
		cur = con.cursor()
		cur.execute(f'SELECT * FROM {table_name}')
		return cur.fetchall()

	def get_distinct_colums(self, table_name, column_name):
		con = sqlite3.connect(self.name)
		cur = con.cursor()
		cmd = f"SELECT DISTINCT {column_name} FROM {table_name}"
		cur.execute(cmd)

		return cur.fetchall()

	def get_value_with_condition(self, table_name, column_name, limit, condition):
		con = sqlite3.connect(self.name)
		cur = con.cursor()
		cur.row_factory = sqlite3.Row
		condition_literals = []
		limit_cmd = f' LIMIT {limit}' if limit > 0 else ''
		base_cmd = f"SELECT {column_name} FROM {table_name}"
		if condition is not None:
			for k, v in condition.items():
				condition_literals.append(f'{k} = "{v}"')

			if len(condition_literals) > 0:
				base_cmd = f"{base_cmd} WHERE {','.join(condition_literals)}"

		base_cmd = f'{base_cmd}{limit_cmd}'
		print(base_cmd)
		cur.execute(base_cmd)
		return cur

	def process_data_from_table(self, table_name, processor, limit, cond=None):
		cur = self.get_value_with_condition(table_name, '*', limit, cond)
		while True:
			row = cur.fetchone()
			if row == None:
				break
			processor(row)

