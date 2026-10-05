from pages.models import MarqueeSetting

def marquee_text(request):
    try:
        slug = request.session.get('selected_branch_slug') or request.COOKIES.get('selected_branch_slug')
        marquee = None
        if slug:
            marquee = MarqueeSetting.objects.filter(active=True, branch__slug=slug).first()
        if not marquee:
            marquee = MarqueeSetting.objects.filter(active=True, branch__isnull=True).first() or MarqueeSetting.objects.filter(active=True).first()
        return {
            'marquee_text': marquee.text if marquee else None
        }
    except Exception:
        return {'marquee_text': None}


def cart(request):
    """Inject the Cart object into every template so the navbar badge is always accurate."""
    try:
        from orders.cart import Cart
        return {'cart': Cart(request)}
    except Exception:
        return {'cart': None}


def branch_context(request):
    """Provide current branch and active branches globally to all templates."""
    try:
        from pages.models import Branch
        all_branches = list(Branch.objects.filter(is_active=True).order_by('order', 'name'))
        
        branch_selected = bool(request.session.get('branch_chosen_in_session'))
        selected_slug = request.session.get('selected_branch_slug') or request.COOKIES.get('selected_branch_slug')
        selected_id = request.session.get('selected_branch_id') or request.COOKIES.get('selected_branch_id')
        
        current_branch = None
        if selected_slug:
            current_branch = next((b for b in all_branches if b.slug == selected_slug), None)
        elif selected_id:
            try:
                bid = int(selected_id)
                current_branch = next((b for b in all_branches if b.id == bid), None)
            except (ValueError, TypeError):
                pass
                
        if not current_branch:
            current_branch = next((b for b in all_branches if b.is_default), None) or (all_branches[0] if all_branches else None)
            
        custom_nav_links = list(current_branch.nav_links.filter(is_active=True).order_by('order', 'id')) if current_branch else []

        return {
            'all_branches': all_branches,
            'current_branch': current_branch,
            'branch_selected_by_user': branch_selected,
            'branch_nav_links': custom_nav_links,
        }
    except Exception:
        return {
            'all_branches': [],
            'current_branch': None,
            'branch_selected_by_user': False,
            'branch_nav_links': [],
        }
