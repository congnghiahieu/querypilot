// This file is auto-generated by @hey-api/openapi-ts

/**
 * Body_upload_file_kb_upload_post
 */
export type BodyUploadFileKbUploadPost = {
  /**
   * File
   */
  file: Blob | File;
};

/**
 * ChatRequest
 */
export type ChatRequest = {
  /**
   * Message
   */
  message: string;
};

/**
 * DataSourceInfo
 */
export type DataSourceInfo = {
  /**
   * Id
   */
  id: string;
  /**
   * Name
   */
  name: string;
  /**
   * Description
   */
  description: string;
  /**
   * Tables
   */
  tables: Array<string>;
  /**
   * Access Level
   */
  access_level: string;
  /**
   * Has Access
   */
  has_access: boolean;
};

/**
 * FileInfo
 */
export type FileInfo = {
  /**
   * Id
   */
  id: string;
  /**
   * Filename
   */
  filename: string;
  /**
   * Original Filename
   */
  original_filename: string;
  /**
   * Size
   */
  size: number;
  /**
   * Upload Date
   */
  upload_date: string;
  /**
   * File Type
   */
  file_type: string;
  /**
   * Processing Status
   */
  processing_status: string;
  /**
   * Has Insight
   */
  has_insight: boolean;
};

/**
 * HTTPValidationError
 */
export type HttpValidationError = {
  /**
   * Detail
   */
  detail?: Array<ValidationError>;
};

/**
 * KnowledgeBaseInsightResponse
 */
export type KnowledgeBaseInsightResponse = {
  /**
   * Summary
   */
  summary: string;
  /**
   * Key Insights
   */
  key_insights: Array<string>;
  /**
   * Entities
   */
  entities: Array<string>;
  /**
   * Topics
   */
  topics: Array<string>;
  /**
   * Processing Time
   */
  processing_time?: number | null;
};

/**
 * KnowledgeBaseResponse
 */
export type KnowledgeBaseResponse = {
  /**
   * Id
   */
  id: string;
  /**
   * Filename
   */
  filename: string;
  /**
   * Original Filename
   */
  original_filename: string;
  /**
   * File Type
   */
  file_type: string;
  /**
   * File Size
   */
  file_size: number;
  /**
   * Upload Date
   */
  upload_date: string;
  /**
   * Processing Status
   */
  processing_status: string;
  /**
   * Download Url
   */
  download_url: string;
  insight?: KnowledgeBaseInsightResponse | null;
};

/**
 * TextUploadRequest
 */
export type TextUploadRequest = {
  /**
   * Text
   */
  text: string;
  /**
   * Title
   */
  title?: string;
};

/**
 * UserCreate
 */
export type UserCreate = {
  /**
   * Username
   */
  username: string;
  /**
   * Password
   */
  password: string;
  /**
   * Email
   */
  email?: string;
  /**
   * Full Name
   */
  full_name?: string;
};

/**
 * UserLogin
 */
export type UserLogin = {
  /**
   * Username
   */
  username: string;
  /**
   * Password
   */
  password: string;
};

/**
 * UserResponse
 */
export type UserResponse = {
  /**
   * Id
   */
  id: string;
  /**
   * Username
   */
  username: string;
  /**
   * Email
   */
  email: string;
  /**
   * Full Name
   */
  full_name: string;
  /**
   * Created At
   */
  created_at: Date;
  /**
   * Role
   */
  role?: string;
};

/**
 * UserSettingsResponse
 */
export type UserSettingsResponse = {
  /**
   * Vai Tro
   */
  vai_tro: string;
  /**
   * Chi Nhanh
   */
  chi_nhanh: string;
  /**
   * Pham Vi
   */
  pham_vi: string;
  /**
   * Du Lieu
   */
  du_lieu: string;
  /**
   * Datasource Permissions
   */
  datasource_permissions: Array<string>;
};

/**
 * UserSettingsUpdate
 */
export type UserSettingsUpdate = {
  /**
   * Vai Tro
   */
  vai_tro: string;
  /**
   * Chi Nhanh
   */
  chi_nhanh: string;
  /**
   * Pham Vi
   */
  pham_vi: string;
  /**
   * Du Lieu
   */
  du_lieu: string;
  /**
   * Datasource Permissions
   */
  datasource_permissions: Array<string>;
};

/**
 * ValidationError
 */
export type ValidationError = {
  /**
   * Location
   */
  loc: Array<string | number>;
  /**
   * Message
   */
  msg: string;
  /**
   * Error Type
   */
  type: string;
};

export type RegisterAuthRegisterPostData = {
  body: UserCreate;
  path?: never;
  query?: never;
  url: '/auth/register';
};

export type RegisterAuthRegisterPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type RegisterAuthRegisterPostError =
  RegisterAuthRegisterPostErrors[keyof RegisterAuthRegisterPostErrors];

export type RegisterAuthRegisterPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ConfirmSignupAuthConfirmSignupPostData = {
  /**
   * Confirmation
   */
  body: {
    [key: string]: unknown;
  };
  path?: never;
  query?: never;
  url: '/auth/confirm-signup';
};

export type ConfirmSignupAuthConfirmSignupPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type ConfirmSignupAuthConfirmSignupPostError =
  ConfirmSignupAuthConfirmSignupPostErrors[keyof ConfirmSignupAuthConfirmSignupPostErrors];

export type ConfirmSignupAuthConfirmSignupPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type LoginAuthLoginPostData = {
  body: UserLogin;
  path?: never;
  query?: never;
  url: '/auth/login';
};

export type LoginAuthLoginPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type LoginAuthLoginPostError = LoginAuthLoginPostErrors[keyof LoginAuthLoginPostErrors];

export type LoginAuthLoginPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type LogoutAuthLogoutPostData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/auth/logout';
};

export type LogoutAuthLogoutPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type RefreshTokenAuthRefreshPostData = {
  /**
   * Refresh Data
   */
  body: {
    [key: string]: unknown;
  };
  path?: never;
  query?: never;
  url: '/auth/refresh';
};

export type RefreshTokenAuthRefreshPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type RefreshTokenAuthRefreshPostError =
  RefreshTokenAuthRefreshPostErrors[keyof RefreshTokenAuthRefreshPostErrors];

export type RefreshTokenAuthRefreshPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ForgotPasswordAuthForgotPasswordPostData = {
  /**
   * Request
   */
  body: {
    [key: string]: unknown;
  };
  path?: never;
  query?: never;
  url: '/auth/forgot-password';
};

export type ForgotPasswordAuthForgotPasswordPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type ForgotPasswordAuthForgotPasswordPostError =
  ForgotPasswordAuthForgotPasswordPostErrors[keyof ForgotPasswordAuthForgotPasswordPostErrors];

export type ForgotPasswordAuthForgotPasswordPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ResetPasswordAuthResetPasswordPostData = {
  /**
   * Request
   */
  body: {
    [key: string]: unknown;
  };
  path?: never;
  query?: never;
  url: '/auth/reset-password';
};

export type ResetPasswordAuthResetPasswordPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type ResetPasswordAuthResetPasswordPostError =
  ResetPasswordAuthResetPasswordPostErrors[keyof ResetPasswordAuthResetPasswordPostErrors];

export type ResetPasswordAuthResetPasswordPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetCurrentUserInfoAuthMeGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/auth/me';
};

export type GetCurrentUserInfoAuthMeGetResponses = {
  /**
   * Successful Response
   */
  200: UserResponse;
};

export type GetCurrentUserInfoAuthMeGetResponse =
  GetCurrentUserInfoAuthMeGetResponses[keyof GetCurrentUserInfoAuthMeGetResponses];

export type NewChatChatNewPostData = {
  body: ChatRequest;
  path?: never;
  query?: never;
  url: '/chat/new';
};

export type NewChatChatNewPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type NewChatChatNewPostError = NewChatChatNewPostErrors[keyof NewChatChatNewPostErrors];

export type NewChatChatNewPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ContinueChatChatContinueChatIdPostData = {
  body: ChatRequest;
  path: {
    /**
     * Chat Id
     */
    chat_id: string;
  };
  query?: never;
  url: '/chat/continue/{chat_id}';
};

export type ContinueChatChatContinueChatIdPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type ContinueChatChatContinueChatIdPostError =
  ContinueChatChatContinueChatIdPostErrors[keyof ContinueChatChatContinueChatIdPostErrors];

export type ContinueChatChatContinueChatIdPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetChatHistoryChatHistoryGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/chat/history';
};

export type GetChatHistoryChatHistoryGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type DeleteChatByIdChatHistoryChatIdDeleteData = {
  body?: never;
  path: {
    /**
     * Chat Id
     */
    chat_id: string;
  };
  query?: never;
  url: '/chat/history/{chat_id}';
};

export type DeleteChatByIdChatHistoryChatIdDeleteErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type DeleteChatByIdChatHistoryChatIdDeleteError =
  DeleteChatByIdChatHistoryChatIdDeleteErrors[keyof DeleteChatByIdChatHistoryChatIdDeleteErrors];

export type DeleteChatByIdChatHistoryChatIdDeleteResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetChatByIdChatHistoryChatIdGetData = {
  body?: never;
  path: {
    /**
     * Chat Id
     */
    chat_id: string;
  };
  query?: never;
  url: '/chat/history/{chat_id}';
};

export type GetChatByIdChatHistoryChatIdGetErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type GetChatByIdChatHistoryChatIdGetError =
  GetChatByIdChatHistoryChatIdGetErrors[keyof GetChatByIdChatHistoryChatIdGetErrors];

export type GetChatByIdChatHistoryChatIdGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetMessageDataChatDataMessageIdGetData = {
  body?: never;
  path: {
    /**
     * Message Id
     */
    message_id: string;
  };
  query?: never;
  url: '/chat/data/{message_id}';
};

export type GetMessageDataChatDataMessageIdGetErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type GetMessageDataChatDataMessageIdGetError =
  GetMessageDataChatDataMessageIdGetErrors[keyof GetMessageDataChatDataMessageIdGetErrors];

export type GetMessageDataChatDataMessageIdGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type DownloadMessageDataChatDownloadMessageIdGetData = {
  body?: never;
  path: {
    /**
     * Message Id
     */
    message_id: string;
  };
  query: {
    /**
     * Format
     */
    format: 'json' | 'csv' | 'excel' | 'pdf';
  };
  url: '/chat/download/{message_id}';
};

export type DownloadMessageDataChatDownloadMessageIdGetErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type DownloadMessageDataChatDownloadMessageIdGetError =
  DownloadMessageDataChatDownloadMessageIdGetErrors[keyof DownloadMessageDataChatDownloadMessageIdGetErrors];

export type DownloadMessageDataChatDownloadMessageIdGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type UploadFileKbUploadPostData = {
  body: BodyUploadFileKbUploadPost;
  path?: never;
  query?: never;
  url: '/kb/upload';
};

export type UploadFileKbUploadPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type UploadFileKbUploadPostError =
  UploadFileKbUploadPostErrors[keyof UploadFileKbUploadPostErrors];

export type UploadFileKbUploadPostResponses = {
  /**
   * Successful Response
   */
  200: KnowledgeBaseResponse;
};

export type UploadFileKbUploadPostResponse =
  UploadFileKbUploadPostResponses[keyof UploadFileKbUploadPostResponses];

export type UploadTextKbKbUploadTextPostData = {
  body: TextUploadRequest;
  path?: never;
  query?: never;
  url: '/kb/upload-text';
};

export type UploadTextKbKbUploadTextPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type UploadTextKbKbUploadTextPostError =
  UploadTextKbKbUploadTextPostErrors[keyof UploadTextKbKbUploadTextPostErrors];

export type UploadTextKbKbUploadTextPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ListKbKbListGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/kb/list';
};

export type ListKbKbListGetResponses = {
  /**
   * Response List Kb Kb List Get
   * Successful Response
   */
  200: Array<FileInfo>;
};

export type ListKbKbListGetResponse = ListKbKbListGetResponses[keyof ListKbKbListGetResponses];

export type GetKbInsightKbKbIdInsightGetData = {
  body?: never;
  path: {
    /**
     * Kb Id
     */
    kb_id: string;
  };
  query?: never;
  url: '/kb/{kb_id}/insight';
};

export type GetKbInsightKbKbIdInsightGetErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type GetKbInsightKbKbIdInsightGetError =
  GetKbInsightKbKbIdInsightGetErrors[keyof GetKbInsightKbKbIdInsightGetErrors];

export type GetKbInsightKbKbIdInsightGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type DeleteKnowledgeBaseKbKbIdDeleteData = {
  body?: never;
  path: {
    /**
     * Kb Id
     */
    kb_id: string;
  };
  query?: never;
  url: '/kb/{kb_id}';
};

export type DeleteKnowledgeBaseKbKbIdDeleteErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type DeleteKnowledgeBaseKbKbIdDeleteError =
  DeleteKnowledgeBaseKbKbIdDeleteErrors[keyof DeleteKnowledgeBaseKbKbIdDeleteErrors];

export type DeleteKnowledgeBaseKbKbIdDeleteResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type DownloadFileKbDownloadKbIdGetData = {
  body?: never;
  path: {
    /**
     * Kb Id
     */
    kb_id: string;
  };
  query?: never;
  url: '/kb/download/{kb_id}';
};

export type DownloadFileKbDownloadKbIdGetErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type DownloadFileKbDownloadKbIdGetError =
  DownloadFileKbDownloadKbIdGetErrors[keyof DownloadFileKbDownloadKbIdGetErrors];

export type DownloadFileKbDownloadKbIdGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetSettingsUserSettingsGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/user/settings';
};

export type GetSettingsUserSettingsGetResponses = {
  /**
   * Successful Response
   */
  200: UserSettingsResponse;
};

export type GetSettingsUserSettingsGetResponse =
  GetSettingsUserSettingsGetResponses[keyof GetSettingsUserSettingsGetResponses];

export type UpdateSettingsUserSettingsPostData = {
  body: UserSettingsUpdate;
  path?: never;
  query?: never;
  url: '/user/settings';
};

export type UpdateSettingsUserSettingsPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type UpdateSettingsUserSettingsPostError =
  UpdateSettingsUserSettingsPostErrors[keyof UpdateSettingsUserSettingsPostErrors];

export type UpdateSettingsUserSettingsPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetDatasourcesUserDatasourcesGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/user/datasources';
};

export type GetDatasourcesUserDatasourcesGetResponses = {
  /**
   * Response Get Datasources User Datasources Get
   * Successful Response
   */
  200: Array<DataSourceInfo>;
};

export type GetDatasourcesUserDatasourcesGetResponse =
  GetDatasourcesUserDatasourcesGetResponses[keyof GetDatasourcesUserDatasourcesGetResponses];

export type GetAccessibleDatasourcesUserDatasourcesAccessibleGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/user/datasources/accessible';
};

export type GetAccessibleDatasourcesUserDatasourcesAccessibleGetResponses = {
  /**
   * Response Get Accessible Datasources User Datasources Accessible Get
   * Successful Response
   */
  200: Array<DataSourceInfo>;
};

export type GetAccessibleDatasourcesUserDatasourcesAccessibleGetResponse =
  GetAccessibleDatasourcesUserDatasourcesAccessibleGetResponses[keyof GetAccessibleDatasourcesUserDatasourcesAccessibleGetResponses];

export type RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostData = {
  body?: never;
  path: {
    /**
     * Datasource Id
     */
    datasource_id: string;
  };
  query?: never;
  url: '/user/datasources/{datasource_id}/request-access';
};

export type RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostErrors = {
  /**
   * Validation Error
   */
  422: HttpValidationError;
};

export type RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostError =
  RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostErrors[keyof RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostErrors];

export type RequestDatasourceAccessUserDatasourcesDatasourceIdRequestAccessPostResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetUserProfileUserProfileGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/user/profile';
};

export type GetUserProfileUserProfileGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type GetUserIamRoleInfoUserIamRoleInfoGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/user/iam-role-info';
};

export type GetUserIamRoleInfoUserIamRoleInfoGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type HealthCheckMetricsHealthGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/metrics/health';
};

export type HealthCheckMetricsHealthGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type RootGetData = {
  body?: never;
  path?: never;
  query?: never;
  url: '/';
};

export type RootGetResponses = {
  /**
   * Successful Response
   */
  200: unknown;
};

export type ClientOptions = {
  baseURL: `${string}://${string}` | (string & {});
};
