from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from market_app.models import Market
from .serializers import MarketSerializer


@api_view(['GET', 'POST'])
def markets_view(request):
    if request.method == 'GET':
        markets = Market.objects.all()
        serializer = MarketSerializer(markets, many=True)
        return Response(serializer.data)

    serializer = MarketSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def market_single_view(request, pk):
    market = get_object_or_404(Market, pk=pk)

    if request.method == 'GET':
        serializer = MarketSerializer(market)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = MarketSerializer(market, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    market.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
