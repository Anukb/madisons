from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import Articles, Category, Notification

@login_required
def edit_article(request, article_id):
    article = get_object_or_404(Articles, id=article_id, author=request.user)
    
    if request.method == 'POST':
        try:
            # Get form data
            title = request.POST.get('title')
            description = request.POST.get('description')
            content = request.POST.get('content')
            category_id = request.POST.get('category')
            status = request.POST.get('status', article.status)  # Keep existing status if not provided
            
            # Validate required fields
            if not all([title, description, content, category_id]):
                return JsonResponse({
                    'success': False,
                    'error': 'Please fill in all required fields.'
                })

            # Update article data
            article.title = title
            article.description = description
            article.content = content
            article.category_id = category_id
            article.status = status

            # Update image only if a new one is provided
            if request.FILES.get('image'):
                article.image = request.FILES['image']
            
            article.save()

            # Create notification
            Notification.objects.create(
                user=request.user,
                title="Article Updated",
                message=f"Your article '{title}' has been updated.",
                is_read=False
            )

            return JsonResponse({
                'success': True,
                'message': 'Article updated successfully!',
                'article_id': article.id
            })

        except Exception as e:
            print(f"Error updating article: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    # For GET request, show the edit form with existing data
    categories = Category.objects.all()
    return render(request, 'write_article.html', {
        'article': article,
        'categories': categories,
        'is_edit': True  # Flag to indicate this is an edit operation
    }) 