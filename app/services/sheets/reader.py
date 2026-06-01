from app.services.sheets.connector import get_worksheet


def get_headers(sheet_connection) -> list[str]:
    ws = get_worksheet(sheet_connection)
    return ws.row_values(sheet_connection.header_row)


def get_all_rows(sheet_connection) -> list[dict]:
    ws = get_worksheet(sheet_connection)
    records = ws.get_all_records(head=sheet_connection.header_row)
    return records


def get_row_by_index(sheet_connection, row_index: int) -> dict:
    ws = get_worksheet(sheet_connection)
    headers = ws.row_values(sheet_connection.header_row)
    values = ws.row_values(sheet_connection.header_row + row_index)
    values += [''] * (len(headers) - len(values))
    return dict(zip(headers, values))


def get_rows_preview(sheet_connection, limit: int = 5) -> list[dict]:
    ws = get_worksheet(sheet_connection)
    all_rows = ws.get_all_records(head=sheet_connection.header_row)
    return all_rows[:limit]
