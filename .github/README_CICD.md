# GitHub Actions CI/CD パイプライン

このドキュメントでは、本プロジェクトのGitHub Actions CI/CDパイプラインの構成と、ecspresso、環境変数、SSMパラメータとの依存関係について説明します。

## 📁 ディレクトリ構成

```
.github/
├── workflows/           # GitHub Actions ワークフロー定義
│   ├── ci-*.yaml       # CI（継続的インテグレーション）
│   ├── deploy-*.yaml   # デプロイメント
│   └── add-issue-to-project.yaml
└── actions/            # カスタムアクション
    ├── build_and_push_*/
    └── deploy_to_ecs_*/
```

## 🔄 ワークフロー概要

### CI ワークフロー
各アプリケーション用のCIワークフローが定義されています：

- [`ci-internal-term.yaml`](.github/workflows/ci-internal-term.yaml) - Internal Term アプリケーション
- [`ci-risk-assessment.yaml`](.github/workflows/ci-risk-assessment.yaml) - Risk Assessment アプリケーション  
- [`ci-securechat.yaml`](.github/workflows/ci-securechat.yaml) - SecureChat アプリケーション

**トリガー条件:**
- `main`ブランチへのpush
- `main`ブランチへのPull Request
- 各アプリケーションディレクトリ内のファイル変更時
- 手動実行（`workflow_dispatch`）

**実行内容:**
- Dockerイメージのビルドテスト
- イメージの検証

### デプロイワークフロー
各アプリケーション用のデプロイワークフローが定義されています：

- [`deploy-internal-term.yaml`](.github/workflows/deploy-internal-term.yaml)
- [`deploy-risk-assessment.yaml`](.github/workflows/deploy-risk-assessment.yaml)
- [`deploy-securechat.yaml`](.github/workflows/deploy-securechat.yaml)

**実行フロー:**
1. **入力検証** - デプロイ対象環境の検証
2. **ビルド&プッシュ** - DockerイメージをECRにプッシュ
3. **デプロイ** - ECSサービスへのデプロイ
4. **通知** - デプロイ結果の通知

## 🛠️ カスタムアクション

### ビルド&プッシュアクション
各アプリケーション用のDockerイメージビルド・ECRプッシュを行います：

- [`build_and_push_internal_term`](.github/actions/build_and_push_internal_term/)
- [`build_and_push_risk_assessment`](.github/actions/build_and_push_risk_assessment/)
- [`build_and_push_securechat`](.github/actions/build_and_push_securechat/)

**主な機能:**
- AWS認証情報の設定
- ECRログイン
- ECRリポジトリの存在確認
- Dockerイメージのビルド・タグ付け・プッシュ

### デプロイアクション
ecspressoを使用してECSへのデプロイを行います：

- [`deploy_to_ecs_internal_term`](.github/actions/deploy_to_ecs_internal_term/)
- [`deploy_to_ecs_risk_assessment`](.github/actions/deploy_to_ecs_risk_assessment/)
- [`deploy_to_ecs_securechat`](.github/actions/deploy_to_ecs_securechat/)

**主な機能:**
- ecspressoのセットアップ
- デプロイ差分の表示（`ecspresso diff`）
- ECSサービスへのデプロイ（`ecspresso deploy`）

## 🔗 ecspressoとの依存関係

### ecspresso設定ファイル
各アプリケーションのecspresso設定は以下に配置されています：

```
ecspresso/
├── internal-term/
│   ├── ecspresso.yaml      # ecspresso設定
│   ├── ecs-service-def.json # ECSサービス定義
│   └── ecs-task-def.json   # ECSタスク定義
├── risk-assessment/
└── securechat/
```

### 必要な環境変数
ecspressoの実行には以下の環境変数が必要です：

#### 共通環境変数
- `STATE_FILE_BUCKET` - Terraformステートファイル用S3バケット名
- `{APP}_IMAGE_TAG` - デプロイするDockerイメージのタグ（通常はGitコミットハッシュ）

#### アプリケーション固有環境変数
- `ECS_CLUSTER_{APP}` - ECSクラスター名
- `ECS_SERVICE_{APP}` - ECSサービス名
- `TARGET_GROUP_ARN_{APP}` - ALBターゲットグループARN

**重要:** これらの環境変数は**GitHub Environments**で管理されており、Terraformステートから直接取得することが困難なため、GitHub ActionsのRepository VariablesまたはEnvironment Variablesとして設定する必要があります。

### Terraformステート参照
ecspressoは[`tfstate`プラグイン](ecspresso/risk-assessment/ecspresso.yaml:13-16)を使用してTerraformステートから以下の情報を取得します：

- ECSタスク定義のファミリー名
- IAMロールARN（実行ロール・タスクロール）
- ECRリポジトリURL
- CloudWatch Logsグループ名
- SSMパラメータARN

ただし、**GitHub Environmentsで管理されている変数**（ECSクラスター名、サービス名、ターゲットグループARNなど）は、Terraformステートから取得するのではなく、GitHub Actionsのワークフロー実行時に環境変数として渡される仕組みになっています。

## 🔐 GitHub Actions環境変数

### Repository Variables と GitHub Environments
GitHub Actionsで使用される環境変数は、以下の2つの方法で管理されています：

1. **Repository Variables** - リポジトリ全体で共通の設定
2. **GitHub Environments** - 環境固有の設定（stg、prodなど）

ecspressoで使用される環境変数の多くは、**GitHub Environments**で環境ごとに管理されているため、Terraformステートから直接参照することができません。そのため、GitHub Actionsのワークフロー実行時に適切な環境の変数が設定される仕組みになっています。

#### AWS関連
- `AWS_ROLE_ARN` - GitHub Actions用IAMロールARN
- `STATE_FILE_BUCKET` - Terraformステートファイル用S3バケット

#### ECR関連
- `ECR_REPOSITORY_INTERNAL_TERM`
- `ECR_REPOSITORY_RISK_ASSESSMENT` 
- `ECR_REPOSITORY_SECURECHAT`

#### ECS関連
- `ECS_CLUSTER_*` - 各アプリケーション用ECSクラスター名
- `ECS_SERVICE_*` - 各アプリケーション用ECSサービス名
- `TARGET_GROUP_ARN_*` - 各アプリケーション用ALBターゲットグループARN

### IAM設定
GitHub Actions用のIAMロールは[`infra/environments/shared/github_actions.tf`](infra/environments/shared/github_actions.tf)で定義されています：

```hcl
module "iam_github_actions" {
  source = "../../modules/iam/github_actions"
  
  role_name               = "imr-ai_gha-shared"
  allowed_repositories    = ["repo:emuni-kyoto/pjt_mh:*"]
  use_minimal_permissions = true
  policy_arns             = []
  tags                    = var.common_tags
}
```

## 🗄️ SSMパラメータとecspressoの関係

### SSMパラメータの管理
アプリケーションの設定値は[AWS Systems Manager Parameter Store](infra/environments/prod/ssm.tf)で管理されています。

### ECSタスク定義での参照
ecspressoのECSタスク定義では、SSMパラメータを`secrets`として参照します：

```json
{
  "secrets": [
    {
      "name": "AWS_ACCESS_KEY_ID",
      "valueFrom": "{{ tfstate `module.ssm_risk_assessment_aws_access_key_id.aws_ssm_parameter.parameter.arn` }}"
    },
    {
      "name": "BEDROCK_REGION",
      "valueFrom": "{{ tfstate `module.ssm_risk_assessment_bedrock_region.aws_ssm_parameter.parameter.arn` }}"
    }
  ]
}
```

### アプリケーション別SSMパラメータ

#### Risk Assessment
- AWS認証情報（`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`）
- Bedrock設定（`BEDROCK_REGION`, `BEDROCK_MODEL_ID_HEAVY`, `BEDROCK_MODEL_ID_LIGHT`）
- Knowledge Base ID（`INTERNAL_KNOWLEDGE_BASE_ID`, `REPORT_KNOWLEDGE_BASE_ID`）
- S3バケット名（`S3_BUCKET_NAME_INTERNAL_RULE`, `S3_BUCKET_NAME_STARTER_TEMPLATES`）

#### SecureChat
- AWS認証情報
- Cognito設定（`COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, `COGNITO_DOMAIN`）
- Chainlit設定（`CHAINLIT_AUTH_SECRET`, `CHAINLIT_URL`）
- OpenAI API Key

#### Internal Term
- OpenAI API Key
- S3バケット名（`S3_BUCKET_NAME_INTERNAL_TERM`, `S3_BUCKET_NAME_STARTER_TEMPLATES`）

### パラメータの更新
SSMパラメータの値は以下の方法で更新できます：

1. **Terraformによる自動設定** - インフラリソースから自動的に設定される値
2. **手動更新** - AWS CLIやコンソールで手動更新が必要な値（API Keyなど）

```bash
# 例：OpenAI API Keyの更新
aws ssm put-parameter \
  --name "/risk-assessment-prod/OPENAI_API_KEY" \
  --value "your-api-key" \
  --type "SecureString" \
  --overwrite
```

## 🚀 デプロイフロー

1. **コード変更** → `main`ブランチにpush
2. **CI実行** → Dockerイメージのビルドテスト
3. **手動デプロイ** → GitHub Actionsから環境を選択してデプロイ実行
4. **ビルド&プッシュ** → DockerイメージをECRにプッシュ
5. **ecspressoデプロイ** → ECSサービスを更新
6. **ヘルスチェック** → サービスの正常性確認
7. **通知** → デプロイ結果の通知

## 🔧 トラブルシューティング

### よくある問題

1. **ECRリポジトリが見つからない**
   - GitHub Repository Variablesの設定を確認
   - ECRリポジトリが正しく作成されているか確認

2. **SSMパラメータが見つからない**
   - Terraformでインフラが正しくデプロイされているか確認
   - パラメータ名の命名規則を確認

3. **ECSデプロイが失敗する**
   - ECSクラスター・サービスの状態を確認
   - タスク定義の設定を確認
   - IAMロールの権限を確認

### ログの確認方法

- **GitHub Actions** - Actions タブでワークフロー実行ログを確認
- **ECS** - CloudWatch Logsでコンテナログを確認
- **ecspresso** - デプロイ時の差分とエラーメッセージを確認

## 📚 関連ドキュメント

- [ecspresso公式ドキュメント](https://github.com/kayac/ecspresso)
- [GitHub Actions公式ドキュメント](https://docs.github.com/en/actions)
- [AWS ECS公式ドキュメント](https://docs.aws.amazon.com/ecs/)
- [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html)

---

## 🧪 デプロイ後スモークテスト仕様

デプロイ後に各アプリケーションの基本機能が正常に動作することを確認するスモークテストの仕様を定義します。

### テスト概要
スモークテストは、デプロイ後にアプリケーションの主要機能をカバーし、システム全体の健全性を迅速に検証するための最小限のテストです。

---

## 🔐 SecureChat スモークテスト

### テスト目的
SecureChatアプリケーションの認証、チャット機能、検索機能、internal-termとの連携、UI表示が正常に動作することを確認する。

### 前提条件
- アプリケーションがデプロイされ、アクセス可能な状態であること
- テスト用のユーザーアカウントが利用可能であること
- internal-termサービスが稼働していること

### テストケース

#### TC-SC-001: ログイン機能テスト
**目的:** ユーザーがアプリケーションに正常にログインできることを確認する

**手順:**
1. SecureChatアプリケーションのURLにアクセス
2. ログイン画面が表示されることを確認
3. 有効なユーザー認証情報を入力
4. ログインボタンをクリック

**期待結果:**
- ログインが成功し、チャット画面に遷移する
- エラーメッセージが表示されない

#### TC-SC-002: チャット応答機能テスト
**目的:** チャット機能が正常に動作し、応答が返ってくることを確認する

**手順:**
1. ログイン後、チャット入力欄に簡単なメッセージを入力（例：「こんにちは」）
2. 送信ボタンをクリックまたはEnterキーを押下

**期待結果:**
- メッセージが送信される
- AIからの応答が返ってくる
- 応答時間が適切な範囲内である

#### TC-SC-003: 検索機能テスト（日付クエリ）
**目的:** 検索機能が正常に動作し、日付に関する質問に回答できることを確認する

**手順:**
1. チャット入力欄に「今日は何日？」と入力
2. 送信ボタンをクリック

**期待結果:**
- 現在の日付情報を含む適切な回答が返される
- 検索機能が正常に動作している

#### TC-SC-004: Internal-Term連携テスト
**目的:** internal-termサービスとの連携が正常に動作することを確認する

**手順:**
1. チャット入力欄に「MHTってなに」と入力
2. 送信ボタンをクリック

**期待結果:**
- internal-termから取得した専門用語の説明が返される
- 連携機能が正常に動作している

#### TC-SC-005: 会話履歴表示テスト
**目的:** 左側のサイドパネルに会話履歴が正常に表示されることを確認する

**手順:**
1. 複数のメッセージを送信
2. 左側のサイドパネルを確認

**期待結果:**
- 過去の会話履歴がサイドパネルに表示される
- 会話履歴が時系列順に整理されている
- 履歴をクリックして過去の会話に戻ることができる

---

## 📊 Risk Assessment スモークテスト

### テスト目的
Risk Assessmentアプリケーションのテンプレート読み込み機能とリスクレポート生成機能が正常に動作することを確認する。

### 前提条件
- アプリケーションがデプロイされ、アクセス可能な状態であること
- starter_templates.jsonファイルがS3に配置されていること

### テストケース

#### TC-RA-001: Starter Templates読み込みテスト
**目的:** starter_templates.jsonが正常に読み込まれ、作業内容選択機能が動作することを確認する

**手順:**
1. Risk AssessmentアプリケーションのURLにアクセス
2. 初期画面で「作業内容を選択してください」の選択肢を確認
3. 利用可能なテンプレートオプションを確認

**期待結果:**
- starter_templates.jsonから読み込まれたテンプレート選択肢が表示される
- 各テンプレートが選択可能な状態である
- エラーメッセージが表示されない

#### TC-RA-002: リスクレポート生成テスト
**目的:** 選択したテンプレートを使用してリスクレポートが正常に生成できることを確認する

**手順:**
1. テンプレート選択画面で任意のテンプレートを選択
2. 必要な情報を入力
3. リスクレポート生成ボタンをクリック

**期待結果:**
- リスクレポートが正常に生成される
- 生成されたレポートが適切な形式で表示される
- 生成プロセス中にエラーが発生しない

---

## 📚 Internal Term スモークテスト

### テスト目的
Internal Termアプリケーションのデータ表示機能、用語登録機能、テンプレートビルダー機能が正常に動作することを確認する。

### 前提条件
- アプリケーションがデプロイされ、アクセス可能な状態であること
- S3バケットにテストデータが配置されていること

### テストケース

#### TC-IT-001: S3データ表示テスト（App）
**目的:** S3からデータをダウンロードして正常に表示できることを確認する

**手順:**
1. Internal Term アプリケーションのメイン画面にアクセス
2. データ表示機能を実行
3. S3から取得されたデータの表示を確認

**期待結果:**
- S3からデータが正常にダウンロードされる
- 取得したデータが適切な形式で画面に表示される
- データの読み込みエラーが発生しない

#### TC-IT-002: 独自用語手動登録テスト（App）
**目的:** 独自用語を手動で登録する機能が正常に動作することを確認する

**手順:**
1. 用語登録画面にアクセス
2. 新しい用語と説明を入力
3. 登録ボタンをクリック
4. 登録された用語が表示されることを確認

**期待結果:**
- 用語が正常に登録される
- 登録した用語が一覧に表示される
- 登録プロセスでエラーが発生しない

#### TC-IT-003: Template Builder機能テスト
**目的:** Template Builderのstarter_templates機能が正常に動作することを確認する

**手順:**
1. Template Builder画面にアクセス
2. starter_templatesの読み込み状況を確認
3. テンプレート編集機能を実行

**期待結果:**
- starter_templatesが正常に読み込まれる
- テンプレートの編集・保存機能が動作する
- 機能実行時にエラーが発生しない

---

## 🚀 スモークテスト実行手順

### 実行タイミング
- 各アプリケーションのデプロイ完了後
- 定期的なヘルスチェック時
- 重要な設定変更後

### 実行順序
1. **Internal Term** - 他のアプリケーションが依存するため最初に実行
2. **SecureChat** - Internal Termとの連携テストを含むため2番目に実行
3. **Risk Assessment** - 独立性が高いため最後に実行

### 実行方法
各テストケースを手動で実行し、結果を記録します。将来的には自動化スクリプトの導入を検討します。

### エラー時の対応
- テスト失敗時は該当アプリケーションのログを確認
- CloudWatch Logsでコンテナログをチェック
- 必要に応じてロールバックを実施

### 成功基準
- 全テストケースが期待結果通りに動作すること
- 応答時間が許容範囲内であること
- エラーログが出力されていないこと