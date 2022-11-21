from django.shortcuts import render, redirect
from .models import Store, StoreImage, Review, ReviewImage, Tag, RestaurantImage, Restaurant
from .forms import ReviewForm, ReviewImageForm, RestaurantForm, RestaurantImageForm
from django.contrib.auth.decorators import login_required
from articles.models import Stadium, Team
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Count, Avg
from django.views.decorators.http import require_http_methods, require_POST, require_safe

@require_safe
def home(request, team_pk):
    team = Team.objects.get(pk=team_pk)
    stadium = Stadium.objects.get(pk=team.stadium_id)
    
    if team.pk == 3:
        middle = Team.objects.filter(stadium_id=team.stadium_id)
        stores = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews')).filter(team=middle[1])
        restaurant = Restaurant.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('restaurant_reviews__grade'), cnt_reviews=Count('restaurant_reviews')).filter(team=middle[1])
    else:
        stores = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews')).filter(team=team)
        restaurant = Restaurant.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('restaurant_reviews__grade'), cnt_reviews=Count('restaurant_reviews')).filter(team=team)

    store_review = stores.order_by('-cnt_reviews')[:5]
    store_following = stores.order_by('-cnt_followings')[:5]
    store_grade = stores.order_by('-avg_grade')[:5]

    restaurant_review = restaurant.order_by('-cnt_reviews')[:5]
    restaurant_following = restaurant.order_by('-cnt_followings')[:5]
    restaurant_grade = restaurant.order_by('-avg_grade')[:5]

    context = {
        'stores': stores,
        "team": team,
        "stadium": stadium,
        # 'restaurants': restaurants,
        # "restaurant_lst": restaurant_lst,
        "store_review": store_review,
        "store_grade": store_grade,
        "store_following": store_following,
        "restaurant_review": restaurant_review,
        "restaurant_grade": restaurant_grade,
        "restaurant_following": restaurant_following,
    }
    return render(request, "foods/home.html", context)

@require_safe
def store_detail(request, team_pk, store_pk):
    team = Team.objects.get(pk=team_pk)
    store = Store.objects.annotate(grade_avg=Avg('store_reviews__grade')).get(pk=store_pk, team=team)
    store.items.replace("등", "")
    items = store.items.split(",")
    lat = float(store.lat)
    lon = float(store.lon)
    review_form = ReviewForm()
    reviewimage_form = ReviewImageForm()
    context = {'team': team, 'store': store, 'review_form': review_form, 'reviewimage_form': reviewimage_form, 'lat': lat, 'lon': lon, 'items': items,}
    return render(request, 'foods/store_detail.html', context)

@require_safe
def store_all(request, team_pk):
    page = request.GET.get("page", "1")
    team = Team.objects.get(pk=team_pk)
    stadium = Stadium.objects.get(pk=team.stadium_id)
    if team.pk == 3:
        middle = Team.objects.filter(stadium_id=team.stadium_id)
        store = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews')).filter(team=middle[1]).order_by('detail')
    else:
        store = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews')).filter(team=team).order_by('detail')
    paginator = Paginator(store, 8)
    page_obj = paginator.get_page(page)
    context = {
        "team":team,
        "stores":page_obj,
        "stadium":stadium,
    }
    return render(request, "foods/store_all.html", context)

@require_POST
def store_follow(request, team_pk, store_pk):
    store = Store.objects.get(pk=store_pk)
    if request.user in store.following_users.all():
        store.following_users.remove(request.user)
        store_follow = False
    else:
        store.following_users.add(request.user)
        store_follow = True
    return JsonResponse(
        {
            "storeFollow": store_follow,
            "storeFollowCount": store.following_users.count(),
        }
    )

@login_required
def store_review_create(request, team_pk, store_pk):
    team = Team.objects.get(pk=team_pk)
    store = Store.objects.get(pk=store_pk, team=team)
    if request.method == "POST":
        review_form = ReviewForm(request.POST, request.FILES)
        reviewimage_form = ReviewImageForm(request.POST, request.FILES)
        images = request.FILES.getlist("image")
        if review_form.is_valid() and reviewimage_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.store_name = store
            if len(images):
                for image in images:
                    image_instance = ReviewImage(review=review, image=image)
                    review.save()
                    image_instance.save()
            else:
                review.save()
            for word in review.content.split():
                if word.startswith('#'):
                    tag, created = Tag.objects.get_or_create(content=word)
                    review.tags.add(tag)
            return redirect("foods:store_detail", team.pk, store.pk)
    else:
        review_form = ReviewForm()
        reviewimage_form = ReviewImageForm()
    context = {
        "review_form": review_form, 
        "reviewimage_form": reviewimage_form
    }
    return render(request, "foods/store_detail.html", context)

@require_POST
def store_review_delete(request, team_pk, store_pk, review_pk):
    team = Team.objects.get(pk=team_pk)
    review = Review.objects.get(pk=review_pk)
    store = Store.objects.get(pk=store_pk)
    review.delete()
    return redirect("foods:store_detail", team.pk, store.pk)

@require_safe
def restaurant_detail(request, team_pk, restaurant_pk):
    team = Team.objects.get(pk=team_pk)
    restaurant = Restaurant.objects.annotate(grade_avg=Avg('restaurant_reviews__grade')).get(pk=restaurant_pk, team=team)
    lat = float(restaurant.lat)
    lon = float(restaurant.lon)
    review_form = ReviewForm()
    reviewimage_form = ReviewImageForm()
    context = {'team': team, 'restaurant': restaurant, 'review_form': review_form, 'reviewimage_form': reviewimage_form, 'lat': lat, 'lon': lon}
    return render(request, 'foods/restaurant_detail.html', context)

@require_safe
def restaurant_all(request, team_pk):
    page = request.GET.get("page", "1")
    team = Team.objects.get(pk=team_pk)
    stadium = Stadium.objects.get(pk=team.stadium_id)
    if team.pk == 3:
        middle = Team.objects.filter(stadium_id=team.stadium_id)
        restaurant = Restaurant.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('restaurant_reviews__grade'), cnt_reviews=Count('restaurant_reviews')).filter(team=middle[1])
    else:
        restaurant = Restaurant.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('restaurant_reviews__grade'), cnt_reviews=Count('restaurant_reviews')).filter(team=team)
    paginator = Paginator(restaurant, 8)
    page_obj = paginator.get_page(page)
    context = {
        "team":team,
        "restaurants":page_obj,
        "stadium":stadium,
    }
    return render(request, "foods/restaurant_all.html", context)

@login_required
def restaurant_follow(request, team_pk, restaurant_pk):
    restaurant = Restaurant.objects.get(pk=restaurant_pk)
    if request.user in restaurant.following_users.all():
        restaurant.following_users.remove(request.user)
        restaurant_follow = False
    else:
        restaurant.following_users.add(request.user)
        restaurant_follow = True
    return JsonResponse(
        {
            "restaurantFollow": restaurant_follow,
            "restaurantFollowCount": restaurant.following_users.count(),
        }
    )

# restaurant를 유저가 직접 쓸 수 있게 하는 페이지, update와 delete는 관리자 권한으로
@login_required
def restaurant_create(request, team_pk):
    team = Team.objects.get(pk=team_pk)
    if request.method == "POST":
        restaurant_form = RestaurantForm(request.POST, request.FILES)
        restaurantimage_form = RestaurantImageForm(request.POST, request.FILES)
        images = request.FILES.getlist("image")
        if restaurant_form.is_valid() and restaurantimage_form.is_valid():
            restaurant = restaurant_form.save(commit=False)
            restaurant.team = team
            if len(images):
                for image in images:
                    image_instance = RestaurantImage(restaurant=restaurant, image=image)
                    restaurant.save()
                    image_instance.save()
            else:
                restaurant.save()
            return redirect("foods:restaurant_detail", team.pk, restaurant.pk)
    else:
        restaurant_form = RestaurantForm()
        restaurantimage_form = RestaurantImageForm()
    context = {
        "restaurant_form": restaurant_form, 
        "restaurantimage_form": restaurantimage_form,
        'team': team,
    }
    return render(request, "foods/restaurant_create.html", context)

@require_POST
def restaurant_review_create(request, team_pk, restaurant_pk):
    team = Team.objects.get(pk=team_pk)
    restaurant = Restaurant.objects.get(pk=restaurant_pk, team=team)
    if request.method == "POST":
        review_form = ReviewForm(request.POST, request.FILES)
        reviewimage_form = ReviewImageForm(request.POST, request.FILES)
        images = request.FILES.getlist("image")
        if review_form.is_valid() and reviewimage_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.restaurant_name = restaurant
            if len(images):
                for image in images:
                    image_instance = ReviewImage(review=review, image=image)
                    review.save()
                    image_instance.save()
            else:
                review.save()
            for word in review.content.split():
                if word.startswith('#'):
                    tag, created = Tag.objects.get_or_create(content=word)
                    review.tags.add(tag)
            return redirect("foods:restaurant_detail", team.pk, restaurant.pk)
    else:
        review_form = ReviewForm()
        reviewimage_form = ReviewImageForm()
    context = {
        "review_form": review_form, 
        "reviewimage_form": reviewimage_form
    }
    return render(request, "foods/restaurant_detail.html", context)

@require_POST
def restaurant_review_delete(request, team_pk, restaurant_pk, review_pk):
    team = Team.objects.get(pk=team_pk)
    review = Review.objects.get(pk=review_pk)
    restaurant = Restaurant.objects.get(pk=restaurant_pk)
    review.delete()
    return redirect("foods:restaurant_detail", team.pk, restaurant.pk)

# store과 restaurant의 태그를 모두 아우름
# 아예 그냥 store과 restaurant를 반으로 나눌까
def tag(request, team_pk, tag_pk):
    team = Team.objects.get(pk=team_pk)
    tag = Tag.objects.get(pk=tag_pk)
    store = Store.objects.filter(team=team)
    restaurant = Restaurant.objects.filter(team=team)
    reviews = []
    for review in tag.tag_articles.all():
        if review.store_name in store:
            reviews.append(review)
    for review in tag.tag_articles.all():
        if review.restaurant_name in restaurant:
            reviews.append(review)
    context={'team': team, 'tag': tag, 'reviews': reviews}
    return render(request, 'foods/tag.html', context)

def search(request, team_pk):
    searched = request.GET.get("searched", False)
    field = request.GET.get("field")
    team = Team.objects.get(pk=team_pk)
    stadium = Stadium.objects.get(pk=team.stadium_id)
    # 내부 매장
    if field == "1":
        result = Store.objects.annotate(cnt_followings=Count('following_users'), avg_grade=Avg('store_reviews__grade'), cnt_reviews=Count('store_reviews')).filter(Q(team=team) & (Q(name__contains=searched) | Q(items__contains=searched)))
    # 외부 가게
    elif field == "2":
        result = Restaurant.objects.filter(Q(team=team) & (Q(name__contains=searched) | Q(content__contains=searched)))
    # 리뷰
    elif field == "3":
        result = Review.objects.filter(Q(team=team) & (Q(content__contains=searched))).order_by("-pk")
    if not searched:
        result = []
        text = "검색어를 입력하세요."
    elif len(result) == 0:
        text = "검색 결과가 없습니다."
    else:
        text = "검색 결과"
    print(result)
    context = {
        "result": result,
        "text": text,
        'field': field,
        'team' : team,
        'searched': searched,
        'stadium': stadium,
    }
    return render(request, "foods/search.html", context)
    