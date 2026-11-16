from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from market_app.models import Market, Product, Seller


class ProductApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.market = Market.objects.create(
            name='Edeka Center', location='Köln', description='Big store', net_worth='250000.00'
        )
        cls.other_market = Market.objects.create(
            name='Rewe City', location='Berlin', description='Small store', net_worth='90000.00'
        )
        cls.seller = Seller.objects.create(name='Fresh Farm', contact_info='farm@example.com')
        cls.seller.markets.set([cls.market, cls.other_market])
        cls.product = Product.objects.create(
            name='Apple',
            description='Red apple',
            price='0.99',
            market=cls.market,
            seller=cls.seller,
        )
        cls.list_url = reverse('product-list')
        cls.detail_url = reverse('product-detail', args=[cls.product.pk])
        cls.missing_url = reverse('product-detail', args=[9999])

    def valid_payload(self, **overrides):
        payload = {
            'name': 'Banana',
            'description': 'Yellow banana',
            'price': '1.49',
            'market': self.market.pk,
            'seller': self.seller.pk,
        }
        payload.update(overrides)
        return payload

    def test_list_returns_products(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['market'], 'Edeka Center')
        self.assertEqual(response.data[0]['seller'], 'Fresh Farm')

    def test_list_uses_constant_queries(self):
        Product.objects.create(
            name='Pear', description='Green pear', price='1.10',
            market=self.other_market, seller=self.seller,
        )

        with self.assertNumQueries(1):
            response = self.client.get(self.list_url)

        self.assertEqual(len(response.data), 2)

    def test_create_product(self):
        response = self.client.post(self.list_url, self.valid_payload(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['market'], 'Edeka Center')
        self.assertEqual(response.data['seller'], 'Fresh Farm')
        product = Product.objects.get(pk=response.data['id'])
        self.assertEqual(product.price, Decimal('1.49'))
        self.assertEqual(product.market, self.market)
        self.assertEqual(product.seller, self.seller)

    def test_create_with_unknown_market_returns_400(self):
        response = self.client.post(self.list_url, self.valid_payload(market=9999), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['market'], ['Market with this id does not exist.'])
        self.assertEqual(Product.objects.count(), 1)

    def test_create_with_unknown_seller_returns_400(self):
        response = self.client.post(self.list_url, self.valid_payload(seller=9999), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['seller'], ['Seller with this id does not exist.'])
        self.assertEqual(Product.objects.count(), 1)

    def test_create_with_missing_fields_returns_400(self):
        response = self.client.post(self.list_url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            set(response.data), {'name', 'description', 'price', 'market', 'seller'}
        )

    def test_create_with_too_many_decimal_places_returns_400(self):
        response = self.client.post(self.list_url, self.valid_payload(price='1.234'), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)

    def test_create_with_negative_price_returns_400(self):
        response = self.client.post(self.list_url, self.valid_payload(price='-0.01'), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('price', response.data)
        self.assertEqual(Product.objects.count(), 1)

    def test_retrieve_product(self):
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.product.pk)
        self.assertEqual(response.data['name'], 'Apple')
        self.assertEqual(response.data['price'], '0.99')

    def test_retrieve_missing_product_returns_404(self):
        response = self.client.get(self.missing_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        payload = self.valid_payload(name='Green Apple', price='1.19', market=self.other_market.pk)

        response = self.client.put(self.detail_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['market'], 'Rewe City')
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Green Apple')
        self.assertEqual(self.product.price, Decimal('1.19'))
        self.assertEqual(self.product.market, self.other_market)

    def test_update_with_missing_fields_returns_400(self):
        response = self.client.put(self.detail_url, {'name': 'Green Apple'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Apple')

    def test_delete_product(self):
        response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b'')
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_delete_missing_product_returns_404(self):
        response = self.client.delete(self.missing_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
