def paginate(query_fn, page, per_page=20, *args):
    offset = (page - 1) * per_page
    items = query_fn(limit=per_page, offset=offset, *args)
    return items

def get_pagination(total, page, per_page=20):
    total_pages = max(1, (total + per_page - 1) // per_page)
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }
