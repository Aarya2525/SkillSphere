import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService, LoginResponse, User } from './auth.service';
import { environment } from '../../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('login should store tokens in localStorage on success', () => {
    const mockResponse: LoginResponse = { access: 'test_access_token', refresh: 'test_refresh_token' };

    service.login({ username: 'testuser', password: 'password123' }).subscribe(res => {
      expect(res).toEqual(mockResponse);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/token/`);
    expect(req.request.method).toBe('POST');
    req.flush(mockResponse);

    expect(service.getAccessToken()).toBe('test_access_token');
    expect(service.getRefreshToken()).toBe('test_refresh_token');
    expect(service.isLoggedIn()).toBeTrue();
  });

  it('getCurrentUser should store user in localStorage on success', () => {
    const mockUser: User = { id: 1, username: 'testuser', email: 'test@example.com', role: 'STUDENT' };

    service.getCurrentUser().subscribe(user => {
      expect(user).toEqual(mockUser);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);

    expect(service.getCurrentUserSnapshot()).toEqual(mockUser);
  });

  it('logout should clear localStorage tokens and user', () => {
    localStorage.setItem('skillsphere_access_token', 'token');
    localStorage.setItem('skillsphere_refresh_token', 'refresh');
    localStorage.setItem('skillsphere_current_user', JSON.stringify({ id: 1 }));

    service.logout();

    expect(service.getAccessToken()).toBeNull();
    expect(service.getRefreshToken()).toBeNull();
    expect(service.getCurrentUserSnapshot()).toBeNull();
    expect(service.isLoggedIn()).toBeFalse();
  });

  it('refreshToken should post refresh token and store new access token', () => {
    localStorage.setItem('skillsphere_refresh_token', 'valid_refresh_token');

    service.refreshToken().subscribe(res => {
      expect(res.access).toBe('new_access_token_456');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/token/refresh/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ refresh: 'valid_refresh_token' });
    req.flush({ access: 'new_access_token_456' });

    expect(service.getAccessToken()).toBe('new_access_token_456');
  });

  it('refreshToken should share in-flight request when called concurrently', () => {
    localStorage.setItem('skillsphere_refresh_token', 'valid_refresh_token');

    let res1: any;
    let res2: any;

    service.refreshToken().subscribe(res => res1 = res);
    service.refreshToken().subscribe(res => res2 = res);

    const reqs = httpMock.match(`${environment.apiUrl}/auth/token/refresh/`);
    expect(reqs.length).toBe(1);
    reqs[0].flush({ access: 'shared_access_token' });

    expect(res1).toEqual({ access: 'shared_access_token' });
    expect(res2).toEqual({ access: 'shared_access_token' });
    expect(service.getAccessToken()).toBe('shared_access_token');
  });

  it('refreshToken should throw error if no refresh token available', (done) => {
    service.refreshToken().subscribe({
      next: () => fail('should have failed'),
      error: (err) => {
        expect(err.message).toBe('No refresh token available');
        done();
      }
    });
  });
});
