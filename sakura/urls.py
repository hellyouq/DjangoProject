from django.urls import path

from sakura import views

urlpatterns = [
    path("", views.home, name="home"),
    path("cases/", views.cases_view, name="cases"),
    path("case/<slug:slug>/", views.case_detail, name="case"),
    path("case/<slug:slug>/open/", views.open_case, name="open_case"),
    path("girl/<slug:slug>/", views.girl_detail, name="girl"),
    path("collection/", views.collection, name="collection"),
    path("market/", views.market, name="market"),
    path("market/sell/", views.sell, name="sell"),
    path("market/buy/<int:pk>/", views.buy, name="buy"),
    path("market/cancel/<int:pk>/", views.cancel, name="cancel"),
    path("profile/", views.profile, name="profile"),
    path("hall/", views.hall, name="hall"),
    path("daily/", views.claim_daily, name="daily"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("art/avatar/<int:seed>.svg", views.avatar_art, name="art_avatar"),
    path("art/case/<str:art_key>.svg", views.case_art, name="art_case"),
    path("art/logo.svg", views.logo, name="art_logo"),
]
